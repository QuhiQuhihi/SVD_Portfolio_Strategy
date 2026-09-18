"""Performance, forecast losses, and paired dependent-data uncertainty."""

import numpy as np
import pandas as pd

ANNUALIZATION = 252


def performance(returns: pd.DataFrame) -> pd.DataFrame:
    if len(returns) < 2 or not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Performance requires at least two complete return rows")
    wealth = (1 + returns).cumprod()
    peaks = wealth.cummax().clip(lower=1.0)
    volatility = returns.std(ddof=1) * np.sqrt(ANNUALIZATION)
    return pd.DataFrame(
        {
            "observations": len(returns),
            "cagr": wealth.iloc[-1] ** (ANNUALIZATION / len(returns)) - 1,
            "annualized_volatility": volatility,
            "annualized_mean_over_volatility_rf0": returns.mean() * ANNUALIZATION / volatility,
            "max_drawdown": (wealth / peaks - 1).min(),
            "terminal_wealth": wealth.iloc[-1],
        }
    )


def paired_block_interval(
    a,
    b,
    *,
    statistic: str = "volatility_difference",
    samples: int = 2000,
    block_length: int = 21,
    seed: int = 20260917,
) -> dict:
    """Circular moving-block bootstrap of paired daily observations.

    Conditional on the realized strategy paths; does not rerun model selection or
    estimate uncertainty across universes/regimes. Bounds are percentile intervals.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Bootstrap inputs must be finite, paired one-dimensional arrays")
    if len(a) < max(30, 2 * block_length) or block_length < 1 or samples < 1:
        raise ValueError("Insufficient observations or invalid bootstrap settings")
    if statistic == "volatility_difference":

        def measure(x, y):
            return (x.std(axis=-1, ddof=1) - y.std(axis=-1, ddof=1)) * np.sqrt(ANNUALIZATION)
    elif statistic == "mean_difference":

        def measure(x, y):
            return (x - y).mean(axis=-1)
    else:
        raise ValueError("Unknown statistic")
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(samples):
        starts = rng.integers(0, len(a), size=int(np.ceil(len(a) / block_length)))
        indices = ((starts[:, None] + np.arange(block_length)) % len(a)).ravel()[: len(a)]
        estimates.append(float(measure(a[indices], b[indices])))
    lower, upper = np.quantile(estimates, [0.025, 0.975])
    return {
        "estimate": float(measure(a, b)),
        "lower_95": float(lower),
        "upper_95": float(upper),
        "observations": len(a),
        "block_length": block_length,
        "samples": samples,
    }


def period_masks(index: pd.DatetimeIndex, test_start: str):
    return {
        "all_oos": np.ones(len(index), dtype=bool),
        "development": np.asarray(index < pd.Timestamp(test_start)),
        "historical_test": np.asarray(index >= pd.Timestamp(test_start)),
    }


def result_tables(
    result, benchmark: pd.Series, test_start: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    net = result.net_returns.assign(**{benchmark.name: benchmark})
    metrics, annual = [], []
    for period, mask in period_masks(net.index, test_start).items():
        if mask.sum() < 2:
            continue
        subset = net.loc[mask]
        table = performance(subset)
        table["gross_annualized_volatility"] = result.gross_returns.loc[mask].std(ddof=1) * np.sqrt(
            ANNUALIZATION
        )
        table["annual_traded_notional"] = result.traded_notional.loc[mask].mean() * ANNUALIZATION
        table["annual_cost_fraction_sum"] = result.costs.loc[mask].mean() * ANNUALIZATION
        table["period"], table["first_date"], table["last_date"] = (
            period,
            subset.index[0],
            subset.index[-1],
        )
        table["daily_return_correlation_with_reference"] = subset.corrwith(benchmark.loc[mask])
        metrics.append(table.rename_axis("strategy").reset_index())
    for year, subset in net.groupby(net.index.year):
        table = performance(subset)
        table["year"], table["first_date"], table["last_date"] = (
            year,
            subset.index[0],
            subset.index[-1],
        )
        table["compounded_period_return"] = (1 + subset).prod() - 1
        annual.append(table.rename_axis("strategy").reset_index())
    return pd.concat(metrics, ignore_index=True), pd.concat(annual, ignore_index=True)
