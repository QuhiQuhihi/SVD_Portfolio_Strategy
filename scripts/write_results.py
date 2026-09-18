"""Regenerate compact evidence tables and the blog's result block from verified artifacts."""

import json
from pathlib import Path

import pandas as pd

from svd_portfolio.config import UNIVERSES
from svd_portfolio.data import sha256
from svd_portfolio.research import source_fingerprint

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
    for key, universe in UNIVERSES.items():
        directory = ROOT / "outputs" / key
        manifest = json.loads((directory / "manifest.json").read_text())
        if manifest["source_sha256"] != source_fingerprint(ROOT):
            raise ValueError(
                "Code changed since execution; rerun notebooks before writing conclusions"
            )
        if manifest["uv_lock_sha256"] != sha256(ROOT / "uv.lock"):
            raise ValueError("Dependency lock changed since execution")
        if not manifest["sensitivity_run"]:
            raise ValueError("Run all declared sensitivities before writing conclusions")
        for name, expected in manifest["tables_sha256"].items():
            if sha256(directory / name) != expected:
                raise ValueError(f"Result hash mismatch: {directory / name}")
        metrics = pd.read_csv(directory / "metrics.csv")
        test = metrics.query("period == 'historical_test'").set_index("strategy")
        intervals = pd.read_csv(directory / "volatility_intervals.csv")
        interval = intervals.query(
            "period == 'historical_test' and comparator == 'Ledoit-Wolf GMV' and block_length == 21"
        ).iloc[0]
        pca, lw = test.loc["PCA GMV"], test.loc["Ledoit-Wolf GMV"]
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
            f"{int((robustness[universe.title] < 0).sum())}/10 declared specifications. "
            f"Its mean QLIKE difference versus Ledoit–Wolf is {qlike.estimate:+.4f} "
            f"(95% interval [{qlike.lower_95:+.4f}, {qlike.upper_95:+.4f}])."
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
    header = """# Results: SVD covariance models and portfolio risk

Executed historical ETF data, January 2, 2025–August 31, 2026: **416 test sessions**.
Primary: 504-session window, rank 3, 30% cap, monthly rebalancing, 5 bps per dollar traded.
Development portfolio evaluation: August 3, 2020–December 31, 2024.
Price snapshots: July 2, 2018–August 31, 2026, 2,052 prices per instrument.

This is a retrospective historical test, not a genuinely untouched holdout. Negative differences
favor PCA. Intervals are pointwise paired circular block-bootstrap percentile intervals with
21-session blocks and 2,000 resamples. They are conditional on the realized portfolio paths.

"""
    text = header + overview_text + "\n\n" + inference_text + "\n\n" + "\n\n".join(detailed)
    text += (
        "\n\n## Sensitivity\n\nPCA minus Ledoit–Wolf annualized volatility, percentage points.\n\n"
    )
    text += robust_text
    text += """

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
"""
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
