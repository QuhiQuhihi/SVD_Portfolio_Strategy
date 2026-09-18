"""Monthly decisions, next-close execution, drift, and self-financing costs."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .config import STRATEGIES, ResearchConfig
from .models import capped_proportional, covariance_models, minimum_variance


@dataclass
class BacktestResult:
    net_returns: pd.DataFrame
    gross_returns: pd.DataFrame
    traded_notional: pd.DataFrame
    costs: pd.DataFrame
    target_weights: pd.DataFrame
    daily_weights: pd.DataFrame
    diagnostics: pd.DataFrame
    risk_forecasts: pd.DataFrame


def rebalance_cost(pretrade, target, cost_bps: float) -> tuple[float, float]:
    """Cost and traded notional as fractions of pre-trade NAV.

    Solve c = rate * sum(abs((1-c)*target - pretrade)). Targets are fractions
    of post-cost NAV. pretrade can sum to zero on the initial cash-funded trade.
    """
    pretrade, target = np.asarray(pretrade, dtype=float), np.asarray(target, dtype=float)
    if pretrade.shape != target.shape or target.ndim != 1:
        raise ValueError("Weight dimensions do not match")
    if not np.isfinite(pretrade).all() or not np.isfinite(target).all():
        raise ValueError("Weights must be finite")
    if pretrade.min() < -1e-10 or target.min() < -1e-10:
        raise ValueError("Only long-only trading is supported")
    if pretrade.sum() > 1 + 1e-8 or abs(target.sum() - 1) > 1e-8:
        raise ValueError("Invalid portfolio budget")
    if not 0 <= cost_bps < 10000:
        raise ValueError("Invalid transaction cost")
    rate = cost_bps / 10000
    if rate == 0:
        return 0.0, float(np.abs(target - pretrade).sum())
    fee = brentq(lambda c: c - rate * np.abs((1 - c) * target - pretrade).sum(), 0, 1)
    return fee, float(np.abs((1 - fee) * target - pretrade).sum())


def run_backtest(returns: pd.DataFrame, config: ResearchConfig) -> BacktestResult:
    """Information through d-1 -> trade at close d -> first exposure return d+1.

    An existing portfolio earns day d's return before its trade at close d.
    The weight cap is an at-rebalance constraint; weights may drift above it.
    """
    if not isinstance(returns.index, pd.DatetimeIndex) or returns.index.has_duplicates:
        raise ValueError("Returns need unique dates")
    if not returns.index.is_monotonic_increasing or returns.columns.has_duplicates:
        raise ValueError("Returns must be sorted with unique tickers")
    if not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError("Invalid returns; missing observations must not be filled")
    n = returns.shape[1]
    if n * config.weight_cap < 1 - 1e-12:
        raise ValueError("Infeasible weight cap")
    dates, values = returns.index, returns.to_numpy()
    months = dates.to_period("M")
    month_start = np.r_[True, np.asarray(months[1:] != months[:-1])]
    candidates = np.flatnonzero(month_start & (dates >= pd.Timestamp(config.evaluation_start)))
    eligible = candidates[candidates >= config.lookback]
    if len(eligible) == 0:
        raise ValueError("No evaluation dates with sufficient training history")
    start = int(eligible[0])
    if start != int(candidates[0]):
        raise ValueError("Insufficient warmup at evaluation_start; use a common later start")
    rows, columns = len(dates) - start, len(STRATEGIES)
    net, gross, turnover, costs = [np.zeros((rows, columns)) for _ in range(4)]
    holdings = np.zeros((columns, n))
    target_records, weight_records, diagnostic_records, forecast_records = [], [], [], []
    current_covariances, forecast_mean, information_date = None, None, None
    previous_loadings = None
    equal = np.full(n, 1 / n)
    for t in range(start, len(dates)):
        out = t - start
        date, day_returns = dates[t], values[t]
        # Save the weights that actually earn today's close-to-close return.
        for j, strategy in enumerate(STRATEGIES):
            weight_records.append(
                {
                    "date": date,
                    "strategy": strategy,
                    **dict(zip(returns.columns, holdings[j], strict=True)),
                }
            )
        if current_covariances is not None:
            residual = float(equal @ day_returns - forecast_mean)
            for estimator, covariance in current_covariances.items():
                variance = float(equal @ covariance @ equal)
                forecast_records.append(
                    {
                        "date": date,
                        "estimator": estimator,
                        "information_date": information_date,
                        "predicted_variance": variance,
                        "realized_squared_residual": residual**2,
                        "qlike": np.log(variance) + residual**2 / variance,
                    }
                )
        for j in range(columns):
            gross[out, j] = holdings[j] @ day_returns
            holdings[j] = holdings[j] * (1 + day_returns) / (1 + gross[out, j])
        if month_start[t]:
            training = returns.iloc[t - config.lookback : t]  # excludes execution date
            current_covariances, pca = covariance_models(
                training,
                config.n_components,
                config.pca_space,
            )
            information_date = training.index[-1]
            forecast_mean = float(training.mean().to_numpy() @ equal)
            targets = [
                equal,
                capped_proportional(1 / training.std(ddof=1).to_numpy(), config.weight_cap),
                *[
                    minimum_variance(current_covariances[name], config.weight_cap)
                    for name in ("Sample", "Ledoit-Wolf", "PCA")
                ],
            ]
            for j, (strategy, target) in enumerate(zip(STRATEGIES, targets, strict=True)):
                fee, traded = rebalance_cost(holdings[j], target, config.cost_bps)
                costs[out, j], turnover[out, j] = fee, traded
                holdings[j] = target
                target_records.append(
                    {
                        "date": date,
                        "strategy": strategy,
                        **dict(zip(returns.columns, target, strict=True)),
                    }
                )
            k = config.n_components
            stability = (
                np.nan
                if previous_loadings is None
                else np.linalg.norm(previous_loadings.T @ pca.loadings[:, :k], "fro") ** 2 / k
            )
            diagnostic_records.append(
                {
                    "execution_date": date,
                    "training_start": training.index[0],
                    "information_date": information_date,
                    "training_rows": len(training),
                    "pc1_variance_share": pca.explained_variance_ratio[0],
                    "retained_variance_share": pca.explained_variance_ratio[:k].sum(),
                    "subspace_overlap": stability,
                    "sample_condition_number": np.linalg.cond(current_covariances["Sample"]),
                    "pca_condition_number": np.linalg.cond(current_covariances["PCA"]),
                    "lw_condition_number": np.linalg.cond(current_covariances["Ledoit-Wolf"]),
                    "pc1_pc2_eigenvalue_ratio": pca.eigenvalues[0] / pca.eigenvalues[1],
                }
            )
            previous_loadings = pca.loadings[:, :k]
        net[out] = (1 + gross[out]) * (1 - costs[out]) - 1

    def frame(x):
        return pd.DataFrame(x, index=dates[start:], columns=STRATEGIES)

    return BacktestResult(
        frame(net),
        frame(gross),
        frame(turnover),
        frame(costs),
        pd.DataFrame(target_records).set_index(["date", "strategy"]),
        pd.DataFrame(weight_records).set_index(["date", "strategy"]),
        pd.DataFrame(diagnostic_records).set_index("execution_date"),
        pd.DataFrame(forecast_records).set_index(["date", "estimator"]),
    )


def buy_and_hold(returns: pd.Series, evaluation_index: pd.DatetimeIndex, cost_bps: float):
    """Reference ETF bought at the same first execution close; no subsequent trading."""
    aligned = returns.loc[evaluation_index].copy()
    fee, _ = rebalance_cost(np.zeros(1), np.ones(1), cost_bps)
    aligned.iloc[0] = -fee
    return aligned
