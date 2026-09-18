"""Readable notebook figures and conclusions derived from executed results."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

COLORS = {
    "Equal weight": "#7b8794",
    "Inverse volatility": "#9c755f",
    "Sample GMV": "#e69f00",
    "Ledoit-Wolf GMV": "#0072b2",
    "PCA GMV": "#009e73",
}
STYLES = {
    "Equal weight": ":",
    "Inverse volatility": "-.",
    "Sample GMV": "--",
    "Ledoit-Wolf GMV": "--",
    "PCA GMV": "-",
}


def set_style():
    plt.rcParams.update(
        {
            "figure.figsize": (10, 5),
            "figure.dpi": 110,
            "savefig.dpi": 160,
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "legend.frameon": False,
        }
    )


def summary_markdown(study: dict) -> str:
    test = study["metrics"].query("period == 'historical_test'").set_index("strategy")
    block_length = study["manifest"]["config"]["block_length"]
    intervals = (
        study["intervals"]
        .query(
            "period == 'historical_test' and comparator == 'Ledoit-Wolf GMV' "
            "and block_length == @block_length",
            local_dict={"block_length": block_length},
        )
        .iloc[0]
    )
    pca, lw = test.loc["PCA GMV"], test.loc["Ledoit-Wolf GMV"]
    crosses = intervals.lower_95 <= 0 <= intervals.upper_95
    inference = (
        "The interval includes zero: this does not distinguish PCA from shrinkage."
        if crosses
        else "The interval excludes zero, conditional on these realized paths; "
        "it is not evidence of a universal advantage."
    )
    dates = f"{str(pca.first_date)[:10]} to {str(pca.last_date)[:10]}"
    return (
        f"**Historical test: {dates} ({int(pca.observations):,} sessions).** "
        f"Net annualized volatility is **{pca.annualized_volatility:.2%} for PCA** versus "
        f"**{lw.annualized_volatility:.2%} for Ledoit–Wolf**. "
        f"PCA minus Ledoit–Wolf: **{intervals.estimate * 100:+.3f} percentage points**, "
        f"with a paired 95% block-bootstrap interval "
        f"**[{intervals.lower_95 * 100:+.3f}, {intervals.upper_95 * 100:+.3f}] pp**. "
        f"{inference}\n\n"
        f"PCA net CAGR is {pca.cagr:.2%}, versus {lw.cagr:.2%} for Ledoit–Wolf. "
        "Lower volatility alone does not establish a superior investment. "
        "This is a retrospective historical test, using current-vintage adjusted prices. "
        "All reported sensitivity variants are exploratory, and the intervals are pointwise."
    )


def plot_performance(study: dict, title: str):
    net = study["result"].net_returns.assign(**{study["reference"].name: study["reference"]})
    # Include wealth before initial funding so the initial cost is visible in drawdown.
    wealth = (1 + net).cumprod()
    before = pd.DataFrame(1.0, index=[net.index[0] - pd.Timedelta(days=1)], columns=net.columns)
    wealth = pd.concat([before, wealth])
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout="constrained")
    for name in wealth:
        axes[0].plot(
            wealth.index,
            wealth[name],
            label=name,
            color=COLORS.get(name, "#332288"),
            ls=STYLES.get(name, ":"),
            lw=2 if name == "PCA GMV" else 1.4,
        )
        drawdown = wealth[name] / wealth[name].cummax() - 1
        axes[1].plot(
            drawdown.index,
            drawdown,
            color=COLORS.get(name, "#332288"),
            ls=STYLES.get(name, ":"),
            lw=2 if name == "PCA GMV" else 1.4,
        )
    for axis in axes:
        axis.axvline(
            pd.Timestamp(study["manifest"]["config"]["test_start"]), color="#555555", lw=1, ls="--"
        )
    axes[0].set(title=f"{title}: wealth after transaction costs", ylabel="Wealth ($1 initial)")
    axes[0].legend(ncols=3, fontsize=9, loc="upper left")
    axes[1].set(title="Drawdown from running peak", ylabel="Drawdown", xlabel="Date")
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    return fig


def plot_intervals(study: dict, title: str):
    config = study["manifest"]["config"]
    block_length = config["block_length"]
    table = study["intervals"].query(
        "period == 'historical_test' and block_length == @block_length"
    )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    groups = (
        ("Simple allocation controls", ["Equal weight", "Inverse volatility"]),
        ("Covariance controls (expanded scale)", ["Sample GMV", "Ledoit-Wolf GMV"]),
    )
    for ax, (panel_title, comparators) in zip(axes, groups, strict=True):
        subset = table.set_index("comparator").loc[comparators]
        for position, row in enumerate(subset.itertuples()):
            ax.plot(
                [row.lower_95 * 100, row.upper_95 * 100],
                [position, position],
                color="#0072b2",
                lw=3,
            )
            ax.scatter(row.estimate * 100, position, color="#009e73", s=60, zorder=3)
            ax.annotate(
                f"{row.estimate * 100:+.3f} pp",
                (row.estimate * 100, position),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                fontsize=10,
            )
        ax.axvline(0, color="#555555", ls="--", lw=1)
        ax.set_yticks(range(len(subset)), comparators)
        ax.set_ylim(len(subset) - 0.5, -0.5)
        ax.set(title=panel_title, xlabel="Annualized volatility difference (pp)")
    fig.suptitle(f"{title}: PCA minus comparator, historical test", fontsize=13)
    fig.text(
        0.5,
        -0.03,
        f"Negative favors PCA. Different panel scales. Pointwise 95% block intervals: "
        f"{block_length} sessions, {config['bootstrap_samples']:,} resamples.",
        ha="center",
        fontsize=9,
    )
    return fig


def plot_factor_diagnostics(study: dict, title: str):
    diagnostics = study["result"].diagnostics
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, layout="constrained")
    axes[0].plot(
        diagnostics.index,
        diagnostics.pc1_variance_share,
        label="First component",
        color="#0072b2",
        ls="--",
    )
    axes[0].plot(
        diagnostics.index,
        diagnostics.retained_variance_share,
        label=f"Retained {study['manifest']['config']['n_components']} components",
        color="#009e73",
    )
    axes[0].set(
        title=f"{title}: rolling training-window factor structure",
        ylabel="Variance share",
        ylim=(0, 1),
    )
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].legend()
    axes[1].plot(diagnostics.index, diagnostics.subspace_overlap, color="#0072b2")
    axes[1].set(
        title="Subspace overlap across consecutive fits",
        ylabel="Overlap (0–1)",
        xlabel="Execution date",
        ylim=(0, 1.02),
    )
    return fig


def plot_weights(study: dict, title: str):
    weights = study["result"].target_weights.xs("PCA GMV", level="strategy")
    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    heatmap = ax.imshow(
        weights.T,
        aspect="auto",
        cmap="Blues",
        vmin=0,
        vmax=study["manifest"]["config"]["weight_cap"],
    )
    ticks = np.arange(0, len(weights), 6)
    ax.set_xticks(ticks, weights.index[ticks].strftime("%Y-%m"), rotation=45, ha="right")
    ax.set_yticks(np.arange(weights.shape[1]), weights.columns)
    ax.set(title=f"{title}: PCA portfolio targets", xlabel="Execution month", ylabel="ETF")
    ax.grid(False)
    fig.colorbar(heatmap, ax=ax, label="Portfolio weight", format=PercentFormatter(1))
    return fig


def plot_sensitivity(study: dict, title: str):
    table = study["sensitivity"].query("period == 'historical_test'")
    if table.empty:
        raise ValueError("Run sensitivity=True to draw this figure")
    pivot = table.pivot(index="variant", columns="strategy", values="annualized_volatility")
    difference = (pivot["PCA GMV"] - pivot["Ledoit-Wolf GMV"]) * 100
    labels = {
        "primary": "Primary specification",
        "rank_1": "1 factor",
        "rank_5": "5 factors",
        "lookback_126": "126-session window",
        "lookback_252": "252-session window",
        "correlation_pca": "Correlation-space PCA",
        "cost_0bps": "0 bps trading cost",
        "cost_10bps": "10 bps trading cost",
        "cap_20pct": "20% position cap",
        "cap_50pct": "50% position cap",
    }
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    ax.barh([labels[key] for key in difference.index], difference, color="#0072b2")
    ax.axvline(0, color="#555555", lw=1)
    ax.invert_yaxis()
    ax.set(
        title=f"{title}: sensitivity of historical-test risk difference",
        xlabel="PCA minus Ledoit–Wolf annualized volatility (percentage points)",
    )
    fig.text(
        0.5,
        -0.03,
        "One setting changes at a time; matching constraints and costs within each "
        "comparison. No winner selection.",
        ha="center",
        fontsize=9,
    )
    return fig


def plot_forecasts(study: dict, title: str):
    daily = study["result"].risk_forecasts.reset_index()
    daily = daily[daily.date >= study["manifest"]["config"]["test_start"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for estimator, group in daily.groupby("estimator"):
        monthly = (
            group.set_index("date")
            .resample("ME")[
                [
                    "predicted_variance",
                    "realized_squared_residual",
                ]
            ]
            .mean()
        )
        axes[0].plot(
            monthly.index,
            np.sqrt(monthly.predicted_variance * 252),
            label=estimator,
            color=COLORS[f"{estimator} GMV"],
            ls=STYLES[f"{estimator} GMV"],
        )
    realized = monthly.realized_squared_residual
    axes[0].plot(
        realized.index, np.sqrt(realized * 252), label="Realized RMS proxy", color="#555555", ls=":"
    )
    axes[0].set(title="Common equal-weight portfolio", ylabel="Annualized volatility proxy")
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].legend(fontsize=9)
    axes[0].tick_params(axis="x", rotation=45)
    table = study["forecast_intervals"].query("period == 'historical_test'")
    for i, row in enumerate(table.itertuples()):
        axes[1].plot([row.lower_95, row.upper_95], [i, i], lw=3, color="#0072b2")
        axes[1].scatter(row.estimate, i, color="#009e73", s=50, zorder=3)
    axes[1].set_yticks(range(len(table)), table.comparator)
    axes[1].axvline(0, color="#555555", ls="--", lw=1)
    axes[1].set(
        title="PCA minus comparator: mean QLIKE", xlabel="Loss difference (negative favors PCA)"
    )
    fig.suptitle(f"{title}: historical-test risk forecasts", fontsize=13)
    return fig


def takeaways_markdown(study: dict) -> str:
    subset = study["sensitivity"].query("period == 'historical_test'")
    pivot = subset.pivot(index="variant", columns="strategy", values="annualized_volatility")
    delta = pivot["PCA GMV"] - pivot["Ledoit-Wolf GMV"]
    targets = study["result"].target_weights.xs("PCA GMV", level="strategy")
    targets = targets[targets.index >= study["manifest"]["config"]["test_start"]]
    largest = targets.mean().nlargest(3)
    exposures = ", ".join(f"{ticker} {weight:.1%}" for ticker, weight in largest.items())
    forecast = (
        study["forecast_intervals"]
        .query("period == 'historical_test' and comparator == 'Ledoit-Wolf'")
        .iloc[0]
    )
    return (
        f"**Stability:** PCA has lower test-period volatility in {int((delta < 0).sum())} "
        f"of {len(delta)} declared specifications. This count is descriptive; the variants share "
        "data and are not independent replications.\n\n"
        f"**Allocation:** the three largest average test-period PCA targets are {exposures}. "
        "Assess whether the risk difference comes from economically meaningful diversification "
        "or concentrated defensive exposures.\n\n"
        f"**Forecasting:** the PCA-minus-Ledoit–Wolf QLIKE difference is {forecast.estimate:+.4f}, "
        f"with a 95% interval [{forecast.lower_95:+.4f}, {forecast.upper_95:+.4f}]. "
        "The common-portfolio forecast test separates estimation quality "
        "from allocation choices.\n\n"
        "**Limits:** fixed ETF selection, overlapping asset exposures, current-vintage data, "
        "one short retrospective test, simplified costs, and pointwise conditional intervals. "
        "The 2020 crash is in training, not in the evaluated portfolio history. "
        "There is no expected-return model or risk-matched alpha claim.\n\n"
        "**Next falsification:** freeze this specification, record it before new observations "
        "arrive, and evaluate a prospective sample. Extend the universe and add exposure-matched "
        "comparators before claiming generality."
    )
