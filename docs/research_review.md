# Review of the original SVD portfolio project

Reviewed: both original notebooks and the [published post](https://quhiquhihi.github.io/posts/SVD_and_Portfolio/).
The unchanged notebook copies are in `archive/`.

## Assessment

The original is a useful linear-algebra demonstration. It does not yet supply the evidence a
quant research reviewer needs to evaluate an investment hypothesis. It shows a decomposition
and an attractive historical comparison, but does not separate estimation from evaluation,
define an investable implementation, or quantify uncertainty.

The largest improvement is a better question, not adding a more complicated machine-learning
model. A credible negative finding, supported by clean experiments and explicit limits, is
more useful than an impressive in-sample cumulative-return chart.

## Consequential findings

Cell numbers below are zero-based and refer to the archived notebooks.

| Finding | Evidence | Why it matters | Revision |
|---|---|---|---|
| Full-sample fitting and evaluation | Equity cell 4 / multi-asset cell 5 fit SVD on every return; later cells apply those weights over the same dates | Future information influences earlier portfolio returns | Rolling training windows, recorded information dates, delayed trading |
| Asset labels disagree with data order | Saved returns are alphabetically ordered, while manually supplied `labels` follow a different order | The plots attribute exposures and correlations to the wrong sectors/assets; the weights used in multiplication themselves follow the returned columns | Tickers are the authoritative labels throughout |
| Non-executable equity cell | Equity cell 5 contains `print("First Eigen portfolio weight = "weight_factor_1)` | Saved output does not establish that the current notebook can run | Complete clean-kernel execution and automated tests |
| Arbitrary leverage | Both notebooks divide weighted returns by `sqrt(S[0])` | The scaling depends on sample length and variance units; it does not define a capital budget or tradable volatility target | Fully invested portfolios, explicit constraints, no singular-value leverage |
| No training centering | Direct `svd(returns)` | This decomposes an uncentered second moment; describing it as covariance PCA is imprecise | Subtract training means; distinguish covariance PCA from correlation PCA |
| Absolute eigenvector weights | `abs(VT[0]) / sum(abs(VT[0]))` | Taking absolute values can destroy a factor's long/short structure; the leading component maximizes variance rather than minimizing portfolio risk | Use loadings to estimate covariance, then solve a stated allocation problem |
| Implicit daily resetting | Constant weights applied to daily returns | This implies daily rebalancing without costs; no drift or executable trade schedule is modeled | Monthly rebalancing, daily drift, explicit buy/sell costs |
| Cumulative-level correlations | Final cells correlate cumulative wealth paths | Shared trends can give misleadingly high correlations; this is not tracking-error or daily-return evidence | Daily returns, risk forecasts and paired comparisons |
| Weak comparison design | PCA curve compared with SPY/AOM, without a matched risk budget | A different defensive/equity mix can explain apparent success | Same-universe controls; references clearly labeled as context |
| No uncertainty or robustness | One window and one factor | The reader cannot distinguish a stable effect from selection or sampling noise | Historical test, block intervals, complete sensitivity table |
| Missing reproducibility contract | No dependencies, tests, snapshot provenance or markdown narrative | Results cannot be reliably audited or rerun | `uv.lock`, shared package, strict data audit, tests, executed notebooks |

The multi-asset equal-weight calculation is algebraically a daily equal-weight gross return;
its central defect is undisclosed daily rebalancing without costs, not that the formula is wrong.
The notebooks' code correctly uses squared singular values for variance shares; the post's
written formula uses unsquared values and should be corrected.

## Mathematical and editorial corrections to the post

For a time-by-asset return matrix, columns of **V** are asset-space directions; **U** contains
time-space directions. The domain/codomain description in the post is reversed. Singular
values are nonnegative. For a symmetric matrix they equal absolute eigenvalues; equality
without absolute values requires positive semidefiniteness, as in a covariance matrix.

The explained-variance share is `s_i² / sum(s_j²)` for centered data. Capturing a fraction of
the return matrix's total variance does not mean a portfolio constructed from an eigenvector
captures that fraction of another portfolio's variance, nor that it tracks SPY. A 750-by-10
example must have ten asset columns, not five. The original code uses three years of history,
whereas the conclusion mentions five. Selecting ten drivers from ten starting ETFs is not
evidence of reducing the number of holdings. ETFs should not be described as ten individual
equities. The sector list omits XLRE; the revised experiment explicitly adds it.

## A stronger question and title

**Title:** *Does SVD Improve Portfolio Risk? Walk-Forward Evidence from Sector and Multi-Asset ETFs*

**Question:** Does a low-rank PCA covariance model improve out-of-sample risk forecasts and
minimum-variance allocations relative to sample covariance and Ledoit–Wolf shrinkage, after
trading costs and under the same portfolio constraints?

This is falsifiable, has strong controls, and gives SVD a defensible economic role. It also
permits a negative answer. With only 11–12 ETFs and hundreds of observations, severe
high-dimensional estimation error cannot be assumed; ordinary shrinkage is a demanding control.
The fixed low rank is a restriction to test, not a benefit to assert.

An alternative project would ask whether a **small, constrained ETF basket replicates a benchmark**
out of sample. That would need an explicit tracking-error objective, a cardinality or sparsity
constraint, and suitable supervised baselines. Unsupervised PCA alone does not solve that
problem. The revised implementation chooses the risk-estimation question consistently instead
of mixing tracking, alpha, and risk reduction claims.

## What makes the revised work more useful in an interview

The reader can inspect exactly what was known at a decision date, reproduce each trade, see
why the covariance estimator is positive semidefinite, and challenge the residual-correlation
assumption. The experiment compares a theoretically appealing estimator with practical
alternatives and reports when its advantage disappears. It distinguishes statistical evidence,
economic materiality, and portfolio exposure.

For a stronger follow-up, freeze the protocol before collecting a genuinely future sample;
extend to an independently selected universe; add exposure-matched controls; and investigate
why covariance-space and correlation-space PCA behave differently. If tuning rank or lookback,
use nested chronological validation and retain a final untouched evaluation. Do not pick the
best variant from this project's historical-test sensitivity table and relabel it confirmatory.

The implementation is a substantial improvement as a research sample. It is still a compact
ETF study, not a new mathematical method or proof of a deployable investment edge.
