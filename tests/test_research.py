"""Financial/accounting and information-timing invariants, using synthetic test fixtures."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from svd_portfolio.backtest import buy_and_hold, rebalance_cost, run_backtest
from svd_portfolio.config import ResearchConfig
from svd_portfolio.data import simple_returns, trading_sessions, validate_prices
from svd_portfolio.metrics import paired_block_interval, performance
from svd_portfolio.models import capped_proportional, minimum_variance, pca_covariance


@pytest.fixture
def returns():
    rng = np.random.default_rng(42)
    common = rng.normal(0, 0.008, (220, 1))
    values = common + rng.normal(0, 0.01, (220, 4))
    return pd.DataFrame(
        values, index=pd.bdate_range("2021-01-01", periods=220), columns=["D", "B", "A", "C"]
    )


@pytest.fixture
def config():
    return ResearchConfig(
        lookback=40,
        n_components=2,
        weight_cap=0.4,
        evaluation_start="2021-04-01",
        bootstrap_samples=100,
    )


def test_pca_centers_and_recovers_full_covariance(returns):
    fit = pca_covariance(returns, 4)
    np.testing.assert_allclose(fit.covariance, returns.cov(), atol=1e-15)
    shifted = pca_covariance(returns + [0.01, -0.02, 0.03, 0.04], 4)
    np.testing.assert_allclose(fit.covariance, shifted.covariance, atol=1e-15)
    assert fit.explained_variance_ratio.sum() == pytest.approx(1)


@pytest.mark.parametrize("space", ["covariance", "correlation"])
def test_factor_covariance_preserves_variances_and_psd(returns, space):
    covariance = pca_covariance(returns, 2, space).covariance
    np.testing.assert_allclose(np.diag(covariance), returns.var(ddof=1), atol=1e-15)
    assert np.linalg.eigvalsh(covariance).min() >= -1e-15
    np.testing.assert_allclose(covariance, pca_covariance(-returns, 2, space).covariance)


def test_analytic_minimum_variance_solution():
    variances = np.array([1.0, 4.0, 9.0])
    expected = (1 / variances) / (1 / variances).sum()
    np.testing.assert_allclose(minimum_variance(np.diag(variances), 1), expected, atol=1e-6)


def test_capped_allocations():
    np.testing.assert_allclose(capped_proportional([9, 9, 2, 2], 0.3), [0.3, 0.3, 0.2, 0.2])
    weights = minimum_variance(np.diag([1, 4, 9, 16]), 0.3)
    assert weights.max() <= 0.3 + 1e-8
    assert weights.sum() == pytest.approx(1)
    with pytest.raises(ValueError, match="Infeasible"):
        minimum_variance(np.eye(3), 0.3)


def test_fee_is_self_financing():
    rate = 0.001
    fee, notional = rebalance_cost([0, 0], [0.5, 0.5], 10)
    assert fee == pytest.approx(rate / (1 + rate))
    assert notional == pytest.approx(1 / (1 + rate))
    fee, notional = rebalance_cost([1, 0], [0, 1], 10)
    assert fee == pytest.approx(2 * rate / (1 + rate))
    assert fee == pytest.approx(rate * notional)
    fee, notional = rebalance_cost([0.5, 0.5], [0.5, 0.5], 10)
    assert fee == pytest.approx(0)
    assert notional == pytest.approx(0)


def test_future_and_execution_date_do_not_change_current_target(returns, config):
    baseline = run_backtest(returns, config)
    change_date = baseline.diagnostics.index[2]
    perturbed = returns.copy()
    perturbed.loc[change_date:] *= [1.8, 0.2, 1.5, 0.5]
    changed = run_backtest(perturbed, config)
    pd.testing.assert_frame_equal(
        baseline.target_weights.loc[:change_date], changed.target_weights.loc[:change_date]
    )
    pd.testing.assert_frame_equal(
        baseline.net_returns.loc[baseline.net_returns.index < change_date],
        changed.net_returns.loc[changed.net_returns.index < change_date],
    )
    assert (baseline.diagnostics.information_date < baseline.diagnostics.index).all()
    forecasts = baseline.risk_forecasts.reset_index()
    assert (forecasts.information_date < forecasts.date).all()


def test_asset_permutation_preserves_labels_and_returns(returns, config):
    baseline = run_backtest(returns, config)
    reordered = run_backtest(returns[sorted(returns.columns)], config)
    np.testing.assert_allclose(baseline.net_returns, reordered.net_returns, atol=1e-7)
    np.testing.assert_allclose(
        baseline.target_weights[sorted(returns.columns)], reordered.target_weights, atol=1e-6
    )


def test_buy_and_hold_accounting_between_rebalances(returns, config):
    # A 50% cap on two assets forces all methods to hold the same target.
    sample = returns.loc[:"2021-04-16", ["A", "B"]]
    config = replace(config, weight_cap=0.5)
    result = run_backtest(sample, config)
    first = result.net_returns.index[0]
    after_trade = sample.loc[sample.index > first]
    asset_growth = (1 + after_trade).prod().mean()
    expected_wealth = asset_growth / (1 + config.cost_bps / 10000)
    np.testing.assert_allclose((1 + result.net_returns).prod(), expected_wealth, atol=1e-12)
    # No portfolio exposure on its execution day; it starts from cash.
    assert (result.gross_returns.iloc[0] == 0).all()
    np.testing.assert_allclose(result.daily_weights.loc[first], 0)
    assert (result.traded_notional.iloc[1:] == 0).all().all()


def test_costs_reduce_terminal_wealth(returns, config):
    free = run_backtest(returns, replace(config, cost_bps=0))
    paid = run_backtest(returns, replace(config, cost_bps=20))
    assert ((1 + paid.net_returns).prod() < (1 + free.net_returns).prod()).all()
    np.testing.assert_allclose(free.gross_returns, paid.gross_returns)


def test_no_silent_filling_or_duplicate_dates():
    prices = pd.DataFrame(
        {"A": [100.0, np.nan, 102]}, index=pd.bdate_range("2024-01-01", periods=3)
    )
    with pytest.raises(ValueError, match="missing"):
        simple_returns(prices)
    prices["A"] = [100, 101, 102]
    prices.index = [prices.index[0]] * 3
    with pytest.raises(ValueError, match="unique"):
        validate_prices(prices)


def test_drawdown_includes_initial_capital():
    values = pd.DataFrame({"A": [-0.1, 0.0]}, index=pd.bdate_range("2024-01-01", periods=2))
    assert performance(values).loc["A", "max_drawdown"] == pytest.approx(-0.1)


def test_bootstrap_is_paired_and_reproducible(returns):
    result = paired_block_interval(returns.A, returns.A, samples=100, block_length=10)
    assert result["estimate"] == result["lower_95"] == result["upper_95"] == 0
    first = paired_block_interval(returns.A, returns.B, samples=100, seed=7)
    assert first == paired_block_interval(returns.A, returns.B, samples=100, seed=7)
    loss = paired_block_interval(returns.A + 2, returns.A, statistic="mean_difference", samples=50)
    assert loss["estimate"] == pytest.approx(2)
    assert loss["lower_95"] == pytest.approx(2)


def test_reference_entry_cost_and_timing(returns):
    index = returns.index[-20:]
    benchmark = buy_and_hold(returns.A, index, 10)
    assert benchmark.iloc[0] == pytest.approx(-0.001 / 1.001)
    pd.testing.assert_series_equal(benchmark.iloc[1:], returns.A.loc[index[1:]])


def test_calendar_accepts_non_session_bounds():
    sessions = trading_sessions("2018-07-01", "2018-07-08")
    assert list(sessions.strftime("%Y-%m-%d")) == [
        "2018-07-02",
        "2018-07-03",
        "2018-07-05",
        "2018-07-06",
    ]
