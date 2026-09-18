# Research protocol

Protocol fixed for this revision before inspecting the new experiment's results. This is not
preregistration: all dates are historical, and the original project already used some of them.

## Question, mechanism and decision

Does restricting common covariance to a few SVD factors improve subsequent risk allocation?
The proposed benefit is reduced covariance estimation noise; the potential cost is discarding
real cross-asset hedges. The primary comparison is PCA versus Ledoit–Wolf minimum-variance
portfolios, not an expected-return or benchmark-tracking claim.

Primary outcome: the difference in net annualized realized volatility, PCA minus Ledoit–Wolf,
in the historical test. Negative is favorable to PCA. Assess the effect size, return sacrifice,
drawdown, turnover, uncertainty, sensitivity, and exposure before interpreting it economically.
This is a variance objective, not a test of maximizing investor utility.

## Universe, source and dates

| Item | Fixed specification |
|---|---|
| US sectors | XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY |
| Multi-asset | AGG, DIA, GLD, IAGG, IDEV, IEMG, LQD, QQQ, SHY, SPY, TLT, VNQ |
| Context references | SPY for sectors, AOM for multi-asset |
| Price history | 2018-07-01 inclusive to 2026-09-01 exclusive |
| Development evaluation | First eligible execution in August 2020 through December 2024 |
| Retrospective historical test | January 2025 through August 2026 |
| Estimation window | 504 past daily returns |
| Evaluation universe | Fixed ETFs with complete expected NYSE sessions |
| Data | Yahoo Finance `Adj Close`, explicitly `auto_adjust=False`, via yfinance |

XLRE is an explicit expansion of the original ten-sector study; the multi-asset set is retained.
The window starts after all selected funds have price history. This is convenience selection,
not a point-in-time universe-construction exercise. Funds overlap economically, particularly
DIA/SPY/QQQ and the bond funds. The test is short and shares global risks across both universes.

Each ticker is cached separately with retrieval time, provider URL, exact interval and hash.
Validate positive finite prices, unique ordered dates, unique tickers, expected exchange sessions,
and aligned histories. Reject missing observations; do not forward fill or silently shorten the
sample. Flag daily returns exceeding 25% in absolute value for review, without clipping them.
Drop the first undefined percentage return. Store the complete data audit with each run.

Adjusted closes are a current-vintage split/distribution-adjusted total-return proxy, not a
point-in-time vendor archive or a fully specified dividend cash ledger. This revision has not
independently reconciled the prices with a second provider. Exact repeatability relies on retaining
the locally hashed snapshots; a new download can incorporate later vendor corrections.

## Covariance estimators and allocation

Center each asset's returns within the training window. If `X = U S Vᵀ`, then
`sample_covariance = V diag(s²/(T−1)) Vᵀ`. Right singular vectors are asset loadings;
explained variance is `s² / sum(s²)`.

The primary PCA estimator uses three components:

`common = V_k diag(s_k²/(T−1)) V_kᵀ`

`factor_covariance = common + diag(diag(sample_covariance − common))`

This retains every asset's sample variance and discards residual cross-asset covariance. The
matrix is positive semidefinite; tiny negative residual variances due to floating-point error
are floored at zero. It is a factor-plus-diagonal model, not pure rank truncation or a full POET
implementation. No matrix inverse is required by the constrained optimizer.

Correlation-space sensitivity standardizes by **training** standard deviations, applies the same
factor construction, then maps covariance back to return units. Its factor variance shares would
refer to standardized returns. The primary diagnostics use unstandardized covariance-space PCA.

Ledoit–Wolf uses the scikit-learn identity-target implementation. Its `1/T` covariance is rescaled
by `T/(T−1)` to use consistent variance units. This scalar does not alter minimum-variance weights.

For sample, Ledoit–Wolf and PCA, minimize `wᵀΣw` subject to `sum(w)=1` and `0≤w_i≤0.30`.
Scale the objective numerically for SLSQP; use its analytic gradient and check convergence and
feasibility. Do not silently replace failed optimization with equal weighting.

Controls are equal weighting and inverse sample volatility with proportional redistribution
when a cap binds. They share the investment universe, trade dates and costs. Position caps hold
at rebalance, not continuously. SPY/AOM buy-and-hold curves are context references, outside the
asset-level constraints, and are not evidence of alpha or a risk-matched fair comparison.

## Timing and accounting

At the first trading session of a month, indexed `d`:

1. Existing positions earn the close-to-close return on `d` and drift to pre-trade weights.
2. Fit a new model using the 504 returns ending at `d−1`. The strategy therefore has a full
   session to compute targets before the assumed closing trade on `d`.
3. Rebalance at close `d`, charging costs on actual notional bought and sold. New weights earn
   their first asset return on `d+1`.

If `u` is the pre-trade risky-asset weight vector, `w` the target as a fraction of post-cost NAV,
and `a=cost_bps/10000`, solve `c = a × sum(abs((1−c)w − u))`. Cost `c` and traded notional are
fractions of pre-trade NAV. Net daily return is `(1+gross_return)(1−c)−1`. With no trade, weights
drift as `w_i(1+r_i)/(1+wᵀr)`. Initial holdings are cash, so the first day contains the entry cost
but no asset exposure. No financing or short selling is present. Residual cash is zero after entry.

Costs are 5 bps per dollar bought **or** sold; a full rotation trades nearly 200% of NAV, so costs
are not multiplied by a half-turnover convention. Entry is charged, terminal liquidation is not.
Distributions are treated as reinvested through adjusted prices. Fractional holdings and closing
execution are assumed. Market impact, taxes, order size, and spread variation are not modeled.

The full portfolio history continues across the January 2025 split without resetting holdings or
charging another entry fee. Historical-test metrics compound only returns in that slice. Rolling
fits may learn from earlier test dates; nothing beyond the decision's information date is used.

## Measures and uncertainty

- Net CAGR: `product(1+r)^(252/n)−1`; a session-based annualization, not a calendar-day estimate.
- Annualized volatility: sample standard deviation of daily returns times `sqrt(252)`. Export
  gross volatility too, so transaction-cost effects can be inspected separately.
- Drawdown: wealth divided by the running peak, including starting capital of 1, minus 1.
- Turnover: annualized sum of buy-plus-sell notional divided by pre-trade NAV. No division by 2.
- Cost measure: annualized arithmetic sum of daily pre-trade NAV cost fractions; not an exact
  difference between gross and net CAGR.
- The exported annualized mean/volatility ratio uses zero as the cash return. It must not be
  described as a cash-adjusted Sharpe ratio. A proper risk-free series is outside this experiment.
- Annual tables report both annualized metrics and actual compounded subperiod return, with
  the observation count and first/last dates. 2020 and 2026 are partial portfolio years.

For the primary volatility difference, resample paired daily strategy returns in circular
contiguous blocks of 21 sessions, 2,000 replicates, seed 20260917. Report the 2.5th/97.5th percentile
bounds. Also report block lengths 5 and 63 and the other controls; those are secondary comparisons.
Intervals preserve local dependence approximately. They are conditional on the estimated return
paths and do not refit the whole research procedure. Regime nonstationarity, model selection,
universe selection, and overlapping experiments limit their interpretation. All intervals are
pointwise; they do not control a family-wise error rate.

## Risk forecasting apart from allocation

Forecast variance for the same fixed daily equal-weight vector `q` using each estimator:
`v = qᵀΣq`. After each execution close, hold that estimate until the next execution. This means
the execution day's return is scored against the previous model. Compare with the squared
residual of `qᵀr` around the training estimate of its mean. These diagnostic returns represent a
frictionless daily equal-weight mathematical portfolio, not the monthly trading strategy.

Use `log(v) + squared_residual/v`, a QLIKE-equivalent loss for pairwise comparisons. Constants
depending only on the common realized proxy cancel. Smaller is better; a negative level of loss
is not intrinsically bad. Compare paired **daily** losses and bootstrap their mean difference.
The realized/predicted variance ratio aggregates both quantities over the evaluation period.
Daily squared residuals are noisy and may be biased for conditional variance if the training mean
is misspecified. No claim of unbiased latent-volatility measurement is made. Monthly plotting
averages are visualization only, not the sample used for inference.

## Declared robustness checks

Ten specifications per universe, changed one at a time from primary:

| Variant | Change |
|---|---|
| `primary` | 504 sessions, rank 3, covariance PCA, 30% cap, 5 bps |
| `rank_1`, `rank_5` | Number of common factors |
| `lookback_126`, `lookback_252` | Training-window length |
| `correlation_pca` | Standardized training returns |
| `cost_0bps`, `cost_10bps` | Trading cost per dollar |
| `cap_20pct`, `cap_50pct` | Concentration constraint for all constrained portfolios |

Keep evaluation dates constant. Recompute all controls under the matching constraints and costs.
Show all variants, including reversals, without selecting a winner or calling repeated variants
independent evidence. The primary remains fixed; any later tuning needs a fresh evaluation sample.

## References

- [DeMiguel, Garlappi & Uppal (2009)](https://doi.org/10.1093/rfs/hhm075): out-of-sample comparison
  of portfolio models with the 1/N control motivates retaining simple alternatives.
- [Ledoit–Wolf implementation and 2004 reference](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html):
  identity-target linear covariance shrinkage.
- [PCA conventions](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html):
  centering, asset-space components and sample-variance normalization.
- [Patton (2011)](https://doi.org/10.1016/j.jeconom.2010.03.034): evaluating volatility forecasts
  using noisy proxies; supports taking the choice of loss and proxy assumptions seriously.
