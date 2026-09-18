"""Fail-closed provenance and independent saved-path accounting checks."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import UNIVERSES, ResearchConfig
from .data import load_prices, sha256, simple_returns
from .research import source_fingerprint


def verify_manifest(root: Path, key: str, *, require_inputs: bool = True) -> dict:
    directory = root / "outputs" / key
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["source_sha256"] != source_fingerprint(root):
        raise ValueError("Source changed: rerun research before publishing results")
    if manifest["uv_lock_sha256"] != sha256(root / "uv.lock"):
        raise ValueError("Dependency lock changed: rerun research")
    for filename, expected in manifest["tables_sha256"].items():
        if sha256(directory / filename) != expected:
            raise ValueError(f"Result changed: {key}/{filename}")
    if require_inputs:
        for snapshot in manifest["data_audit"]["snapshots"]:
            path = (
                root
                / "data"
                / "raw"
                / (
                    f"{snapshot['ticker']}_{snapshot['start_inclusive']}_"
                    f"{snapshot['end_exclusive']}.csv"
                )
            )
            metadata = json.loads(path.with_suffix(".json").read_text())
            if metadata != snapshot or sha256(path) != snapshot["sha256"]:
                raise ValueError(f"Input vintage changed: {snapshot['ticker']}")
    return manifest


def verify_accounting(root: Path, key: str) -> dict:
    manifest = verify_manifest(root, key)
    universe = UNIVERSES[key]
    config = ResearchConfig(**manifest["config"])
    prices, _ = load_prices(universe, config, root)
    asset_returns = simple_returns(prices).loc[:, list(universe.tickers)]
    directory = root / "outputs" / key
    net, gross, fees, turnover = [
        pd.read_csv(directory / f"{name}.csv", index_col=0, parse_dates=True)
        for name in ("net_returns", "gross_returns", "costs", "traded_notional")
    ]
    weights = pd.read_csv(directory / "daily_weights.csv", parse_dates=["date"])
    targets = pd.read_csv(directory / "target_weights.csv", parse_dates=["date"])
    dates = pd.read_csv(
        directory / "diagnostics.csv", parse_dates=["execution_date", "information_date"]
    )
    if not (dates.information_date < dates.execution_date).all():
        raise ValueError("Information-date leakage")
    for strategy, group in weights.groupby("strategy"):
        earning = group.set_index("date").loc[:, list(universe.tickers)]
        aligned = asset_returns.loc[earning.index]
        independently_gross = (earning * aligned).sum(axis=1)
        np.testing.assert_allclose(gross[strategy], independently_gross, atol=2e-12, rtol=1e-9)
        np.testing.assert_allclose(
            net[strategy],
            (1 + independently_gross) * (1 - fees[strategy]) - 1,
            atol=2e-12,
            rtol=1e-9,
        )
        for row in targets.loc[targets.strategy == strategy].itertuples(index=False):
            target = np.array([getattr(row, ticker) for ticker in universe.tickers])
            if abs(target.sum() - 1) > 1e-8 or target.min() < -1e-8:
                raise ValueError("Invalid target budget")
            if target.max() > config.weight_cap + 1e-8:
                raise ValueError("Target cap violated")
            pretrade = earning.loc[row.date].to_numpy() * (1 + aligned.loc[row.date])
            pretrade = pretrade / (1 + independently_gross.loc[row.date])
            cost = fees.loc[row.date, strategy]
            traded = np.abs((1 - cost) * target - pretrade).sum()
            np.testing.assert_allclose(turnover.loc[row.date, strategy], traded, atol=2e-10)
            np.testing.assert_allclose(cost, traded * config.cost_bps / 10000, atol=2e-12)
    metrics = pd.read_csv(directory / "metrics.csv")
    for row in metrics.query("period == 'historical_test'").itertuples():
        r = net.loc[net.index >= config.test_start, row.strategy]
        np.testing.assert_allclose(
            row.annualized_volatility, r.std(ddof=1) * np.sqrt(252), atol=1e-11
        )
        np.testing.assert_allclose(row.cagr, np.prod(1 + r) ** (252 / len(r)) - 1, atol=1e-10)
    # Independent symmetric eigensolver check for the first recorded PCA risk forecast.
    forecasts = pd.read_csv(
        directory / "risk_forecasts.csv", parse_dates=["date", "information_date"]
    )
    first = forecasts.query("estimator == 'PCA'").iloc[0]
    training = asset_returns.loc[: first.information_date].tail(config.lookback)
    covariance = np.cov(training.to_numpy(), rowvar=False, ddof=1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    retained = eigenvectors[:, -config.n_components :]
    common = (retained * eigenvalues[-config.n_components :]) @ retained.T
    model = common + np.diag(np.diag(covariance - common).clip(min=0))
    equal = np.full(len(universe.tickers), 1 / len(universe.tickers))
    np.testing.assert_allclose(first.predicted_variance, equal @ model @ equal, atol=1e-12)
    return {
        "universe": key,
        "sessions": len(net),
        "strategies": len(gross.columns),
        "rebalances": len(dates),
        "accounting": "passed",
        "eigensolver_check": "passed",
    }
