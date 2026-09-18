"""Run the declared experiment and write inspectable, source-linked artifacts."""

import hashlib
import importlib.metadata
import json
import platform
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .backtest import buy_and_hold, run_backtest
from .config import ResearchConfig, Universe
from .data import load_prices, sha256, simple_returns
from .metrics import paired_block_interval, period_masks, result_tables


def source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "src").rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_study(
    universe: Universe,
    config: ResearchConfig,
    root: Path,
    *,
    download: bool = False,
    refresh: bool = False,
    sensitivity: bool = False,
) -> dict:
    prices, audit = load_prices(universe, config, root, download=download, refresh=refresh)
    returns = simple_returns(prices)
    assets = returns.loc[:, list(universe.tickers)]
    result = run_backtest(assets, config)
    reference = buy_and_hold(returns[universe.benchmark], result.net_returns.index, config.cost_bps)
    reference.name = f"{universe.benchmark} buy & hold"
    metrics, annual = result_tables(result, reference, config.test_start)
    intervals = []
    for period, mask in period_masks(result.net_returns.index, config.test_start).items():
        if mask.sum() < 126:
            continue
        sub = result.net_returns.loc[mask]
        for comparator in ("Equal weight", "Inverse volatility", "Sample GMV", "Ledoit-Wolf GMV"):
            for block in (5, config.block_length, 63):
                interval = paired_block_interval(
                    sub["PCA GMV"],
                    sub[comparator],
                    samples=config.bootstrap_samples,
                    block_length=block,
                    seed=config.seed,
                )
                intervals.append({"period": period, "comparator": comparator, **interval})
    forecast_rows, forecast_intervals = [], []
    forecasts = result.risk_forecasts.reset_index()
    for period, mask in period_masks(
        pd.DatetimeIndex(forecasts["date"]), config.test_start
    ).items():
        subset = forecasts.loc[mask]
        if subset.empty:
            continue
        for estimator, group in subset.groupby("estimator"):
            forecast_rows.append(
                {
                    "period": period,
                    "estimator": estimator,
                    "observations": len(group),
                    "mean_qlike": group.qlike.mean(),
                    "realized_over_predicted_variance": (
                        group.realized_squared_residual.sum() / group.predicted_variance.sum()
                    ),
                }
            )
        pivot = subset.pivot(index="date", columns="estimator", values="qlike")
        if len(pivot) >= max(30, 2 * config.block_length):
            for comparator in ("Sample", "Ledoit-Wolf"):
                interval = paired_block_interval(
                    pivot["PCA"],
                    pivot[comparator],
                    statistic="mean_difference",
                    samples=config.bootstrap_samples,
                    block_length=config.block_length,
                    seed=config.seed,
                )
                forecast_intervals.append({"period": period, "comparator": comparator, **interval})
    out = root / "outputs" / universe.key
    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "net_returns": result.net_returns.assign(**{reference.name: reference}),
        "gross_returns": result.gross_returns,
        "traded_notional": result.traded_notional,
        "costs": result.costs,
        "target_weights": result.target_weights,
        "daily_weights": result.daily_weights,
        "diagnostics": result.diagnostics,
        "risk_forecasts": result.risk_forecasts,
    }
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", float_format="%.12g")
    tables_without_index = {
        "metrics": metrics,
        "annual_metrics": annual,
        "volatility_intervals": pd.DataFrame(intervals),
        "forecast_metrics": pd.DataFrame(forecast_rows),
        "forecast_intervals": pd.DataFrame(forecast_intervals),
    }
    for name, table in tables_without_index.items():
        table.to_csv(out / f"{name}.csv", index=False, float_format="%.12g")
    sensitivity_table = pd.DataFrame()
    if sensitivity:
        sensitivity_table = run_sensitivity(assets, returns[universe.benchmark], config)
        sensitivity_table.to_csv(out / "sensitivity.csv", index=False, float_format="%.12g")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_status": "Retrospective historical test; no genuinely untouched holdout claimed",
        "config": config.to_dict(),
        "data_audit": audit,
        "python": platform.python_version(),
        "source_sha256": source_fingerprint(root),
        "uv_lock_sha256": sha256(root / "uv.lock"),
        "packages": {
            p: importlib.metadata.version(p)
            for p in ("numpy", "pandas", "scipy", "scikit-learn", "yfinance", "exchange-calendars")
        },
        "sensitivity_run": sensitivity,
        "tables_sha256": {
            f"{name}.csv": sha256(out / f"{name}.csv") for name in (*tables, *tables_without_index)
        },
    }
    if sensitivity:
        manifest["tables_sha256"]["sensitivity.csv"] = sha256(out / "sensitivity.csv")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return {
        "prices": prices,
        "audit": audit,
        "result": result,
        "metrics": metrics,
        "annual": annual,
        "intervals": pd.DataFrame(intervals),
        "forecast_metrics": pd.DataFrame(forecast_rows),
        "forecast_intervals": pd.DataFrame(forecast_intervals),
        "reference": reference,
        "sensitivity": sensitivity_table,
        "manifest": manifest,
    }


def sensitivity_configs(base: ResearchConfig) -> dict[str, ResearchConfig]:
    """One-at-a-time ablations; every candidate is reported, none selects a winner."""
    return {
        "primary": base,
        "rank_1": replace(base, n_components=1),
        "rank_5": replace(base, n_components=5),
        "lookback_126": replace(base, lookback=126),
        "lookback_252": replace(base, lookback=252),
        "correlation_pca": replace(base, pca_space="correlation"),
        "cost_0bps": replace(base, cost_bps=0),
        "cost_10bps": replace(base, cost_bps=10),
        "cap_20pct": replace(base, weight_cap=0.20),
        "cap_50pct": replace(base, weight_cap=0.50),
    }


def run_sensitivity(returns: pd.DataFrame, benchmark: pd.Series, base: ResearchConfig):
    records = []
    for name, config in sensitivity_configs(base).items():
        result = run_backtest(returns, config)
        reference = buy_and_hold(benchmark, result.net_returns.index, config.cost_bps)
        reference.name = f"{benchmark.name} buy & hold"
        metrics, _ = result_tables(result, reference, config.test_start)
        metrics["variant"] = name
        for key in ("lookback", "n_components", "weight_cap", "cost_bps", "pca_space"):
            metrics[key] = getattr(config, key)
        records.append(metrics)
    return pd.concat(records, ignore_index=True)
