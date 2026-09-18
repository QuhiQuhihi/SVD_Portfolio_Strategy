"""Adjusted-close snapshots with strict alignment and recoverable provenance."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import exchange_calendars as xcals
import numpy as np
import pandas as pd

from .config import ResearchConfig, Universe


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trading_sessions(start: str, end: str) -> pd.DatetimeIndex:
    """NYSE sessions in [start, end); all instruments are US-listed ETFs."""
    end_date = pd.Timestamp(end) - pd.Timedelta(days=1)
    calendar = xcals.get_calendar("XNYS", start=start, end=end_date)
    index = calendar.sessions
    index = index[(index >= pd.Timestamp(start)) & (index <= end_date)]
    return index.tz_localize(None).rename("Date")


def validate_prices(prices: pd.DataFrame, expected: pd.DatetimeIndex | None = None) -> None:
    if prices.empty or len(prices) < 2 or prices.shape[1] < 1:
        raise ValueError("Need at least two price observations")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Prices require a DatetimeIndex")
    if prices.index.has_duplicates or not prices.index.is_monotonic_increasing:
        raise ValueError("Price dates must be unique and sorted")
    if prices.columns.has_duplicates:
        raise ValueError("Duplicate ticker columns")
    if not np.isfinite(prices.to_numpy(dtype=float)).all() or (prices <= 0).any().any():
        raise ValueError("Prices contain missing, non-finite, or non-positive values")
    if expected is not None and not prices.index.equals(expected):
        missing = expected.difference(prices.index)
        extra = prices.index.difference(expected)
        raise ValueError(f"Session mismatch: missing={list(missing[:5])}, extra={list(extra[:5])}")


def simple_returns(prices: pd.DataFrame) -> pd.DataFrame:
    validate_prices(prices)
    result = prices.pct_change(fill_method=None).iloc[1:]
    if not np.isfinite(result.to_numpy()).all() or (result <= -1).any().any():
        raise ValueError("Invalid simple returns")
    return result


def load_prices(
    universe: Universe,
    config: ResearchConfig,
    root: Path,
    *,
    download: bool = False,
    refresh: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """Read validated cached snapshots. Network access must be explicitly requested.

    Each ticker is checkpointed independently. A rerun resumes from successful files.
    Refresh replaces only the requested date-keyed snapshot, never notebook originals.
    """
    cache = root / "data" / "raw"
    cache.mkdir(parents=True, exist_ok=True)
    expected = trading_sessions(config.data_start, config.data_end)
    series, manifests = [], []
    tickers = tuple(dict.fromkeys((*universe.tickers, universe.benchmark)))
    for ticker in tickers:
        path = cache / f"{ticker}_{config.data_start}_{config.data_end}.csv"
        meta_path = path.with_suffix(".json")
        if refresh or not path.exists() or not meta_path.exists():
            if not download:
                raise FileNotFoundError(
                    f"Missing snapshot for {ticker}. Run: uv run python scripts/run_research.py "
                    "--download --universe all"
                )
            import yfinance as yf

            yf.set_tz_cache_location(str(root / ".cache" / "yfinance"))
            history = yf.Ticker(ticker).history(
                start=config.data_start,
                end=config.data_end,
                interval="1d",
                auto_adjust=False,
                actions=True,
                raise_errors=True,
            )
            if history.empty or "Adj Close" not in history:
                raise RuntimeError(f"No adjusted-close data returned for {ticker}")
            values = history["Adj Close"].copy().rename(ticker)
            values.index = values.index.tz_localize(None).normalize().rename("Date")
            validate_prices(values.to_frame(), expected)
            temporary = path.with_suffix(".tmp")
            values.to_csv(temporary, float_format="%.17g")
            temporary.replace(path)
            metadata = {
                "ticker": ticker,
                "source": "Yahoo Finance via yfinance",
                "source_url": f"https://finance.yahoo.com/quote/{ticker}/history/",
                "field": "Adj Close",
                "auto_adjust": False,
                "interval": "1d",
                "start_inclusive": config.data_start,
                "end_exclusive": config.data_end,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "yfinance_version": yf.__version__,
                "sha256": sha256(path),
                "rows": len(values),
                "first_date": str(values.index[0].date()),
                "last_date": str(values.index[-1].date()),
                "caveat": "Current vintage, split/dividend-adjusted proxy; not point-in-time data.",
            }
            meta_path.write_text(json.dumps(metadata, indent=2) + "\n")
        metadata = json.loads(meta_path.read_text())
        if metadata["sha256"] != sha256(path):
            raise ValueError(f"Snapshot hash mismatch: {path}")
        if (metadata["ticker"], metadata["start_inclusive"], metadata["end_exclusive"]) != (
            ticker,
            config.data_start,
            config.data_end,
        ):
            raise ValueError(f"Snapshot metadata mismatch: {meta_path}")
        values = pd.read_csv(path, index_col="Date", parse_dates=True)
        if list(values.columns) != [ticker]:
            raise ValueError(f"Wrong ticker column: {path}")
        validate_prices(values, expected)
        series.append(values[ticker])
        manifests.append(metadata)
    prices = pd.concat(series, axis=1).loc[:, list(tickers)]
    validate_prices(prices, expected)
    returns = simple_returns(prices)
    audit = {
        "universe": universe.key,
        "price_rows": len(prices),
        "return_rows": len(returns),
        "first_price": str(prices.index[0].date()),
        "last_price": str(prices.index[-1].date()),
        "missing_values": int(prices.isna().sum().sum()),
        "sessions_verified": "XNYS",
        "max_abs_daily_return": returns.abs().max().to_dict(),
        "observations_over_25pct": int((returns.abs() > 0.25).sum().sum()),
        "snapshots": manifests,
    }
    return prices, audit
