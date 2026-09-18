# Results: SVD covariance models and portfolio risk

Executed historical ETF data, January 2, 2025–August 31, 2026: **416 test sessions**.
Primary: 504-session window, rank 3, 30% cap, monthly rebalancing, 5 bps per dollar traded.
Development portfolio evaluation: August 3, 2020–December 31, 2024.
Price snapshots: July 2, 2018–August 31, 2026, 2,052 prices per instrument.

This is a retrospective historical test, not a genuinely untouched holdout. Negative differences
favor PCA. Intervals are pointwise paired circular block-bootstrap percentile intervals with
21-session blocks and 2,000 resamples. They are conditional on the realized portfolio paths.

| Universe | PCA volatility | Ledoit–Wolf volatility | Difference (pp) | 95% CI (pp) |
| --- | --- | --- | --- | --- |
| US sector ETFs | 11.92% | 11.99% | -0.075 | [-0.224, +0.053] |
| Multi-asset ETFs | 3.14% | 3.21% | -0.068 | [-0.113, -0.020] |

- **US sector ETFs:** PCA has lower historical-test volatility in 4/10 declared specifications. Its mean QLIKE difference versus Ledoit–Wolf is -0.0049 (95% interval [-0.0869, +0.0404]).
- **Multi-asset ETFs:** PCA has lower historical-test volatility in 9/10 declared specifications. Its mean QLIKE difference versus Ledoit–Wolf is -0.0131 (95% interval [-0.0577, +0.0164]).

## US sector ETFs

| Portfolio | Net CAGR | Net annualized volatility | Max drawdown | Annual traded NAV |
| --- | --- | --- | --- | --- |
| Equal weight | 16.02% | 13.45% | -15.00% | 0.35× |
| Inverse volatility | 14.77% | 13.06% | -14.15% | 0.35× |
| Sample GMV | 10.62% | 12.04% | -11.38% | 0.80× |
| Ledoit-Wolf GMV | 10.95% | 11.99% | -11.37% | 0.86× |
| PCA GMV | 10.96% | 11.92% | -11.55% | 0.80× |
| SPY buy & hold | 18.92% | 17.32% | -18.76% | — |

## Multi-asset ETFs

| Portfolio | Net CAGR | Net annualized volatility | Max drawdown | Annual traded NAV |
| --- | --- | --- | --- | --- |
| Equal weight | 15.05% | 9.51% | -7.80% | 0.26× |
| Inverse volatility | 8.69% | 5.27% | -4.09% | 0.27× |
| Sample GMV | 4.55% | 3.20% | -2.47% | 0.30× |
| Ledoit-Wolf GMV | 4.67% | 3.21% | -2.46% | 0.31× |
| PCA GMV | 4.49% | 3.14% | -2.24% | 0.36× |
| AOM buy & hold | 11.56% | 7.94% | -6.54% | — |

## Sensitivity

PCA minus Ledoit–Wolf annualized volatility, percentage points.

| Variant | US sector ETFs | Multi-asset ETFs |
| --- | --- | --- |
| cap_20pct | -0.122 | -0.011 |
| cap_50pct | +0.069 | -0.120 |
| correlation_pca | +0.152 | +0.002 |
| cost_0bps | -0.075 | -0.068 |
| cost_10bps | -0.075 | -0.069 |
| lookback_126 | +0.292 | -0.126 |
| lookback_252 | +0.076 | -0.103 |
| primary | -0.075 | -0.068 |
| rank_1 | +0.725 | -0.151 |
| rank_5 | +0.203 | -0.022 |

Variants share observations and are not independent replications. The cost and constraint settings
are matched within each comparison. The declared primary specification is not replaced by the
best-performing variant. Reference ETFs have different exposures;
they are not risk-matched controls.

## Interpretation and source trail

The primary sector result is small and its volatility interval includes zero. Several alternative
settings reverse the sign. The multi-asset effect is small in absolute annualized volatility, and
its primary interval excludes zero, but the portfolio is largely a constrained bond allocation.
In both universes the common-portfolio forecast-loss interval includes zero. These results do not
establish general SVD superiority or alpha.

The notebooks show exposures, rolling factor structure, development/test comparisons and cost-aware
wealth paths. Full daily results, block-length variants and provenance are under `outputs/`.
The results above were regenerated from CSVs after checking their recorded SHA-256 hashes and
the source/dependency fingerprints. Raw inputs are Yahoo Finance adjusted-close snapshots; the
manifests contain individual provider URLs, retrieval timestamps and input hashes. No independent
second-vendor price reconciliation was performed.

Commands: `uv run python scripts/execute_notebooks.py`, then
`uv run python scripts/write_results.py`.
