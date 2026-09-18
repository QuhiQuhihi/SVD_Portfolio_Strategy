"""Rebuild both narrative notebooks from the shared, tested research implementation."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def notebook(key: str, subtitle: str):
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    universe_note = (
        "Eleven US sector ETFs, including XLRE (omitted from the original). SPY is a "
        "market reference, not a same-risk portfolio benchmark."
        if key == "us_equity"
        else "The original twelve multi-asset ETFs are retained. US equity and bond ETFs overlap; "
        "fund count is not a count of independent exposures. AOM is a reference allocation, "
        "not a risk-matched benchmark."
    )
    cells = [
        md(
            f"# Does SVD Improve Portfolio Risk?\n## {subtitle}\n\n"
            "Walk-forward evidence on PCA covariance models, estimation error, and trading costs.\n\n"
            "This notebook is a research experiment, not a return-prediction strategy. "
            "The original 2024 notebook is preserved in `archive/`. "
            "See `docs/research_review.md` for the audit and `docs/research_protocol.md` for definitions."
        ),
        md(
            "## tl;dr\n\nThe next two cells recompute the findings from validated local market-data "
            "snapshots. They never download data silently. First run "
            "`uv run python scripts/run_research.py --download --sensitivity` from the project root. "
            "The saved outputs below are actual executions; synthetic fixtures are used only in tests."
        ),
        code(
            """from pathlib import Path
import os

ROOT = Path.cwd()
assert (ROOT / "pyproject.toml").exists(), "Start Jupyter from the project root."
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import Markdown, display
from svd_portfolio.config import UNIVERSES, ResearchConfig
from svd_portfolio.data import simple_returns
from svd_portfolio.research import run_study
from svd_portfolio.presentation import (
    set_style, summary_markdown, takeaways_markdown, plot_performance,
    plot_intervals, plot_factor_diagnostics, plot_weights, plot_sensitivity, plot_forecasts,
)

CONFIG = ResearchConfig()  # Fixed primary specification; inspect it below.
UNIVERSE = UNIVERSES["""
            + repr(key)
            + """ ]
set_style()
study = run_study(UNIVERSE, CONFIG, ROOT, download=False, sensitivity=True)
FIGURES = ROOT / "outputs" / UNIVERSE.key / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

def show_figure(figure, name):
    figure.savefig(FIGURES / f"{name}.png", bbox_inches="tight")
    figure.savefig(FIGURES / f"{name}.svg", bbox_inches="tight")
    plt.show()
    plt.close(figure)
"""
        ),
        code("display(Markdown(summary_markdown(study)))"),
        md(r"""## Context & Methods

**Question:** does a low-dimensional covariance estimate improve subsequent realized portfolio risk,
relative to sample covariance and Ledoit–Wolf shrinkage, under identical implementation constraints?

**Mechanism:** restricting common covariance to a few factors may reduce estimation error, but can
discard economically useful hedges. More variance explained in training does not establish better
out-of-sample forecasts, benchmark tracking, or returns.

For a rolling $T \times N$ return window, subtract the training column means and compute
$X=USV^\top$. The asset loadings are columns of $V$, and covariance eigenvalues are
$\lambda_i=s_i^2/(T-1)$. Explained variance is $s_i^2/\sum_j s_j^2$.

The factor covariance estimate retains idiosyncratic variances:
$$\widehat\Sigma_k=V_k\Lambda_kV_k^\top+
\operatorname{diag}\{\operatorname{diag}(\widehat\Sigma-V_k\Lambda_kV_k^\top)\}.$$
This assumes the residual cross-asset covariances are zero. We then solve
$$\min_w w^\top\widehat\Sigma_k w\quad\text{subject to}\quad
\mathbf{1}^\top w=1,\;0\leq w_i\leq0.30.$$

**Primary comparison:** net annualized volatility of PCA GMV minus Ledoit–Wolf GMV in the historical
test. Report returns, drawdowns, turnover, gross volatility, and common-portfolio risk forecasts too.
Equal weight and capped inverse volatility are simpler controls; sample GMV isolates covariance
regularization. None of these estimates expected returns.

### Key Assumptions

- Primary: 504 past trading sessions, rank 3, covariance-space PCA, 30% maximum target weight.
- On the first session of each month, use returns through the preceding session, execute at that
  day's close, and earn the new weights' returns from the following session. Existing holdings earn
  the execution day's return before trading. This avoids same-close fitting and execution.
- Hold positions between trades, allowing weights to drift. Charge 5 bps per dollar bought **or**
  sold, including entry. Solve costs self-consistently against post-cost target weights.
- Development evaluation begins August 2020; the retrospective test begins January 2025. The 2020
  crash occurs in the initial training history, not in evaluated strategy returns. Rolling training
  may include earlier test observations; future observations never enter a fit.
- Prices are current-vintage adjusted closes, a total-return proxy. Fractional shares, reinvested
  distributions, and close execution are assumed. Costs do not model market impact or taxes.
- Annualization uses 252 sessions. The mean/volatility ratio in the CSV assumes a zero cash rate
  and is explicitly **not** a properly excess-return Sharpe ratio.

Full protocol, sensitivity choices, and limitations: `docs/research_protocol.md`.
"""),
        code("display(pd.Series(CONFIG.to_dict(), name='Value').to_frame())"),
        md(
            "## Data\n\n" + universe_note + "\n\nSource: Yahoo Finance adjusted daily closes via "
            "yfinance, July 2018–August 2026. Each ticker has a dated CSV and SHA-256 manifest. "
            "We require all expected NYSE sessions, finite positive prices, unique dates and columns, "
            "and complete cross-asset alignment. No forward filling or zero-return imputation. "
            "The complete-sample descriptive table below is never used to choose strategy weights."
        ),
        code("""prices = study["prices"]
returns = simple_returns(prices)
coverage = pd.DataFrame(study["audit"]["snapshots"])[
    ["ticker", "first_date", "last_date", "rows", "retrieved_at_utc"]
].set_index("ticker")
coverage["Daily volatility"] = returns.std()
coverage["Largest absolute daily return"] = returns.abs().max()
display(coverage.style.format({"Daily volatility": "{:.2%}",
                              "Largest absolute daily return": "{:.2%}"}))
print(f"Missing prices: {study['audit']['missing_values']}; "
      f"returns above 25% absolute: {study['audit']['observations_over_25pct']}; "
      f"calendar: {study['audit']['sessions_verified']}.")"""),
        md(
            "## Results\n\n### 1. Performance on identical dates\n\n"
            "The reference ETF has a different risk budget. Use it for context; the covariance-model "
            "comparison is among portfolios with the same constraints. The vertical line marks the "
            "start of the retrospective historical test."
        ),
        code("""metrics = study["metrics"]
test = metrics.query("period == 'historical_test'").set_index("strategy")
columns = {"cagr": "Net CAGR", "annualized_volatility": "Net volatility",
           "max_drawdown": "Max drawdown", "annual_traded_notional": "Traded NAV / year",
           "annual_cost_fraction_sum": "Annual cost sum"}
display(test[list(columns)].rename(columns=columns).style.format({
    "Net CAGR": "{:.2%}", "Net volatility": "{:.2%}", "Max drawdown": "{:.2%}",
    "Traded NAV / year": "{:.2f}×", "Annual cost sum": "{:.3%}"}, na_rep="—"))
show_figure(plot_performance(study, UNIVERSE.title), "performance")"""),
        md(
            "Source: cached Yahoo Finance adjusted-close returns, August 2020–August 2026; "
            "computed by the shared accounting engine. Lower volatility may accompany lower returns "
            "and different market exposure. A visually smoother curve alone is not a successful strategy."
        ),
        md(
            "### 2. How uncertain is the risk difference?\n\n"
            "Compare paired daily net returns in January 2025–August 2026. Resample common contiguous "
            "21-session blocks with wraparound, 2,000 times. Intervals are conditional on the realized "
            "strategy paths and pointwise, with no multiple-comparison adjustment. The CSV also "
            "reports 5- and 63-session block lengths."
        ),
        code("show_figure(plot_intervals(study, UNIVERSE.title), 'volatility_intervals')"),
        md(
            "An interval crossing zero does not resolve which method has lower risk. An interval "
            "excluding zero still needs an economic effect-size and robustness assessment."
        ),
        md(
            "### 3. Does the risk model forecast better?\n\n"
            "Use the **same frictionless daily equal-weight return** for every covariance estimator. "
            "Its squared residual uses the training-window mean. Evaluate "
            r"$\log(\hat v_t)+(r_t-\hat\mu_t)^2/\hat v_t$. Lower QLIKE is better. "
            "The chart compares monthly averages of daily predictions with a noisy realized RMS proxy. "
            "The interval uses daily loss differences; no overlapping forward windows are treated "
            "as independent observations."
        ),
        code("""display(study["forecast_metrics"].query("period == 'historical_test'")
        .drop(columns="period").set_index("estimator").round(4))
show_figure(plot_forecasts(study, UNIVERSE.title), "risk_forecasts")"""),
        md(
            "Variance calibration near one is desirable. This diagnostic controls portfolio weights; "
            "a lower-volatility optimized portfolio by itself cannot establish better forecasts."
        ),
        md(
            "### 4. Factor stability and portfolio concentration\n\n"
            "Variance shares refer to rolling **training** windows. The subspace overlap is "
            r"$\|V_{k,t-1}^{\top}V_{k,t}\|_F^2/k$, invariant to sign changes and rotations within "
            "the retained subspace. Consecutive windows overlap heavily, so stability is descriptive. "
            "It is not predictive evidence."
        ),
        code("show_figure(plot_factor_diagnostics(study, UNIVERSE.title), 'factor_diagnostics')"),
        code("show_figure(plot_weights(study, UNIVERSE.title), 'weights')"),
        md(
            "Source: monthly estimates and targets generated only from prior returns. The cap binds "
            "at rebalance; holdings may drift above it between trades. Read the asset composition "
            "alongside risk improvements, particularly for multi-asset allocations."
        ),
        md(
            "### 5. Falsification through parameter sensitivity\n\n"
            "All ten specifications were declared before this run: primary; ranks 1/5; windows "
            "126/252; correlation-space PCA; costs 0/10 bps; caps 20%/50%. The figure changes one "
            "setting at a time and reports **every** comparison on the same historical-test dates. "
            "These are descriptive ablations, not a search for the best backtest."
        ),
        code("show_figure(plot_sensitivity(study, UNIVERSE.title), 'sensitivity')"),
        md(
            "### 6. Development versus historical test\n\n"
            "A finding that changes across subperiods requires qualification. Annual tables with "
            "explicit first and last dates, including partial years, are saved under `outputs/`."
        ),
        code("""comparison = metrics.query("period != 'all_oos'").pivot(
    index="strategy", columns="period", values="annualized_volatility")
display(comparison.style.format("{:.2%}"))"""),
        md("## Takeaways"),
        code("display(Markdown(takeaways_markdown(study)))"),
        md(
            "### Reproducibility and references\n\n"
            "`outputs/<universe>/manifest.json` records the protocol, package versions, source hash, "
            "data retrieval times, snapshot hashes, and result hashes. All forecasts, trades, targets, "
            "and daily pre-return holdings are exported. Rerunning uses the snapshots; `--refresh` "
            "explicitly requests new vendor data.\n\n"
            "- [DeMiguel, Garlappi & Uppal (2009), Optimal Versus Naive Diversification]"
            "(https://doi.org/10.1093/rfs/hhm075): motivation for simple controls.\n"
            "- [Ledoit–Wolf estimator and reference]"
            "(https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html).\n"
            "- [PCA centering, loadings and variance conventions]"
            "(https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html).\n"
            "- [yfinance price API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html).\n\n"
            "The contribution is an auditable empirical comparison, not a new decomposition algorithm "
            "or a demonstrated source of alpha."
        ),
    ]
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3 (svd research)",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python", "version": "3.12"}
    for i, cell in enumerate(nb.cells):
        cell.id = f"{key}-{i:02d}"
    nbf.validate(nb)
    return nb


def main():
    for filename, key, subtitle in (
        ("SVD-US_Equity.ipynb", "us_equity", "US Sector ETFs"),
        ("SVD-Multi_Asset.ipynb", "multi_asset", "Multi-Asset ETFs"),
    ):
        nbf.write(notebook(key, subtitle), ROOT / filename)
        print(f"Built {filename}")


if __name__ == "__main__":
    main()
