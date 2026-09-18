"""Regenerate compact evidence tables and the blog's result block from verified artifacts."""

from pathlib import Path

import pandas as pd

from svd_portfolio.config import UNIVERSES
from svd_portfolio.validation import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def markdown_table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows],
        ]
    )


def main():
    overview, detailed, robustness, inference = [], [], {}, []
    interpretations = []
    common_sample = None
    common_spec = None
    for key, universe in UNIVERSES.items():
        directory = ROOT / "outputs" / key
        manifest = verify_manifest(ROOT, key)
        if not manifest["sensitivity_run"]:
            raise ValueError("Run all declared sensitivities before writing conclusions")
        metrics = pd.read_csv(directory / "metrics.csv")
        test = metrics.query("period == 'historical_test'").set_index("strategy")
        intervals = pd.read_csv(directory / "volatility_intervals.csv")
        interval = intervals.query(
            "period == 'historical_test' and comparator == 'Ledoit-Wolf GMV' and block_length == 21"
        ).iloc[0]
        pca, lw = test.loc["PCA GMV"], test.loc["Ledoit-Wolf GMV"]
        current_sample = (pca.first_date, pca.last_date, int(pca.observations))
        if common_sample is not None and current_sample != common_sample:
            raise ValueError(
                "Universe evaluation dates differ; cannot write a common-sample header"
            )
        common_sample = current_sample
        development = metrics.query("period == 'development' and strategy == 'PCA GMV'").iloc[0]
        config = manifest["config"]
        audit = manifest["data_audit"]
        spec = (
            config,
            audit["first_price"],
            audit["last_price"],
            audit["price_rows"],
            development.first_date,
            development.last_date,
        )
        if common_spec is not None and spec != common_spec:
            raise ValueError("Universe specifications differ; cannot write a shared header")
        common_spec = spec
        bounds = f"[{100 * interval.lower_95:+.3f}, {100 * interval.upper_95:+.3f}]"
        overview.append(
            [
                universe.title,
                f"{pca.annualized_volatility:.2%}",
                f"{lw.annualized_volatility:.2%}",
                f"{100 * interval.estimate:+.3f}",
                bounds,
            ]
        )
        rows = [
            [
                name,
                f"{r.cagr:.2%}",
                f"{r.annualized_volatility:.2%}",
                f"{r.max_drawdown:.2%}",
                "—" if pd.isna(r.annual_traded_notional) else f"{r.annual_traded_notional:.2f}×",
            ]
            for name, r in test.iterrows()
        ]
        detailed.append(
            f"## {universe.title}\n\n"
            + markdown_table(
                [
                    "Portfolio",
                    "Net CAGR",
                    "Net annualized volatility",
                    "Max drawdown",
                    "Annual traded NAV",
                ],
                rows,
            )
        )
        sensitivity = pd.read_csv(directory / "sensitivity.csv").query(
            "period == 'historical_test'"
        )
        pivot = sensitivity.pivot(
            index="variant", columns="strategy", values="annualized_volatility"
        )
        robustness[universe.title] = (pivot["PCA GMV"] - pivot["Ledoit-Wolf GMV"]) * 100
        qlike = (
            pd.read_csv(directory / "forecast_intervals.csv")
            .query("period == 'historical_test' and comparator == 'Ledoit-Wolf'")
            .iloc[0]
        )
        inference.append(
            f"- **{universe.title}:** PCA has lower historical-test volatility in "
            f"{int((robustness[universe.title] < 0).sum())}/"
            f"{len(robustness[universe.title])} declared specifications. "
            f"Its mean QLIKE difference versus Ledoit–Wolf is {qlike.estimate:+.4f} "
            f"(95% interval [{qlike.lower_95:+.4f}, {qlike.upper_95:+.4f}])."
        )
        interval_status = (
            "includes zero" if interval.lower_95 <= 0 <= interval.upper_95 else "excludes zero"
        )
        forecast_status = (
            "includes zero" if qlike.lower_95 <= 0 <= qlike.upper_95 else "excludes zero"
        )
        interpretations.append(
            f"{universe.title}: the primary volatility interval {interval_status}; "
            f"the common-portfolio forecast-loss interval {forecast_status}. "
            "The effect is conditional on this universe, fitted paths and historical period."
        )
    overview_text = markdown_table(
        ["Universe", "PCA volatility", "Ledoit–Wolf volatility", "Difference (pp)", "95% CI (pp)"],
        overview,
    )
    inference_text = "\n".join(inference)
    robust = pd.DataFrame(robustness)
    robust_text = markdown_table(
        ["Variant", *robust.columns],
        [[name, *[f"{value:+.3f}" for value in row]] for name, row in robust.iterrows()],
    )
    header = f"""# Results: SVD covariance models and portfolio risk

Executed historical ETF data, {common_sample[0][:10]}–{common_sample[1][:10]}:
**{common_sample[2]} test sessions**.
Primary: {config["lookback"]}-session window, rank {config["n_components"]},
{config["weight_cap"]:.0%} cap, monthly rebalancing, {config["cost_bps"]:g} bps per dollar traded.
Development portfolio evaluation: {development.first_date[:10]}–{development.last_date[:10]}.
Price snapshots: {manifest["data_audit"]["first_price"]}–{manifest["data_audit"]["last_price"]},
{manifest["data_audit"]["price_rows"]:,} prices per instrument.

This is a retrospective historical test, not a genuinely untouched holdout. Negative differences
favor PCA. Intervals are pointwise paired circular block-bootstrap percentile intervals with
{config["block_length"]}-session blocks and {config["bootstrap_samples"]:,} resamples.
They are conditional on the realized portfolio paths.

"""
    text = header + overview_text + "\n\n" + inference_text + "\n\n" + "\n\n".join(detailed)
    text += (
        "\n\n## Sensitivity\n\nPCA minus Ledoit–Wolf annualized volatility, percentage points.\n\n"
    )
    text += robust_text
    text += (
        """

Variants share observations and are not independent replications. The cost and constraint settings
are matched within each comparison. The declared primary specification is not replaced by the
best-performing variant. Reference ETFs have different exposures;
they are not risk-matched controls.

## Interpretation and source trail

"""
        + "\n\n".join(interpretations)
        + """

These results do not establish general SVD superiority or alpha. Compare the exposures and
all declared sensitivities before interpreting a change in portfolio volatility economically.

The notebooks show exposures, rolling factor structure, development/test comparisons and cost-aware
wealth paths. Full daily results, block-length variants and provenance are under `outputs/`.
The results above were regenerated from CSVs after checking their recorded SHA-256 hashes and
the source/dependency fingerprints. Raw inputs are Yahoo Finance adjusted-close snapshots; the
manifests contain individual provider URLs, retrieval timestamps and input hashes. No independent
second-vendor price reconciliation was performed.

Commands: `uv run python scripts/execute_notebooks.py`, then
`uv run python scripts/write_results.py`.
"""
    )
    (ROOT / "docs" / "results_summary.md").write_text(text)
    draft = ROOT / "docs" / "blog_draft.md"
    content = draft.read_text()
    start, end = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"
    before, rest = content.split(start, 1)
    _, after = rest.split(end, 1)
    content = (
        before + start + "\n\n" + overview_text + "\n\n" + inference_text + "\n\n" + end + after
    )
    draft.write_text(content)
    print("Updated docs/results_summary.md and the verified results block in docs/blog_draft.md")


if __name__ == "__main__":
    main()
