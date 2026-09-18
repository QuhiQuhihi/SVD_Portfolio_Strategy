"""Render exact mathematical diagrams and a source-backed PCA scree plot for publication.

Creates new vector figures and PNG exports; original blog images are preserved separately.
Market data are read only from validated local snapshots. No network requests are made.
"""

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from svd_portfolio.config import UNIVERSES, ResearchConfig  # noqa: E402
from svd_portfolio.data import load_prices, sha256, simple_returns  # noqa: E402
from svd_portfolio.validation import verify_manifest  # noqa: E402

DESTINATION = ROOT / "docs" / "assets" / "svd"
INK, BLUE, TEAL, ORANGE, GRAY = "#193549", "#dbeafe", "#d1fae5", "#ffedd5", "#e2e8f0"


def save(figure, name):
    figure.savefig(DESTINATION / f"{name}.svg", bbox_inches="tight", facecolor="white")
    figure.savefig(DESTINATION / f"{name}.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def block(ax, center, width, height, symbol, dimensions, role, color):
    x, y = center
    ax.add_patch(
        FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            facecolor=color,
            edgecolor=INK,
            lw=1.3,
        )
    )
    ax.text(x, y + 0.1, symbol, ha="center", va="center", fontsize=28, color=INK)
    ax.text(x, y - height / 2 - 0.28, dimensions, ha="center", va="top", fontsize=12, color=INK)
    ax.text(x, y + height / 2 + 0.22, role, ha="center", va="bottom", fontsize=12, color=INK)


def diagrams():
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.set(xlim=(0, 13), ylim=(0, 5))
    ax.axis("off")
    block(ax, (1.0, 2.45), 1.25, 2.55, "$X$", "$750 \\times 10$", "Centered returns", BLUE)
    block(ax, (4.6, 2.45), 2.55, 2.55, "$U$", "$750 \\times 750$", "Time directions", GRAY)
    block(ax, (8.35, 2.45), 1.25, 2.55, "$S$", "$750 \\times 10$", "Singular values", ORANGE)
    block(ax, (11.6, 2.45), 1.25, 1.25, "$V^\\top$", "$10 \\times 10$", "Asset directions", TEAL)
    for x, symbol in ((2.45, "$=$"), (6.8, "$\\times$"), (9.95, "$\\times$")):
        ax.text(x, 2.45, symbol, ha="center", va="center", fontsize=28, color=INK)
    fig.suptitle("Full SVD: one return matrix, three pieces", fontsize=18, color=INK, y=0.99)
    fig.text(
        0.5, 0.91, "Illustration: 750 daily observations and 10 ETFs", ha="center", fontsize=12
    )
    fig.text(
        0.5,
        0.055,
        "Reduced SVD keeps the exact reconstruction with shapes "
        "(750 × 10) · (10 × 10) · (10 × 10).",
        ha="center",
        fontsize=11,
        color=INK,
    )
    fig.text(
        0.5,
        0.005,
        "Matrix sizes are given by the labels; boxes are schematic.",
        ha="center",
        fontsize=9,
        color="#526477",
    )
    save(fig, "picture1")

    fig, ax = plt.subplots(figsize=(13, 4.7))
    ax.set(xlim=(0, 16), ylim=(0, 5))
    ax.axis("off")
    block(ax, (1.0, 2.4), 1.3, 2.5, "$X$", "$750 \\times 10$", "Original", BLUE)
    block(ax, (4.0, 2.4), 0.85, 2.5, "$U_4$", "$750 \\times 4$", "4 time directions", GRAY)
    block(ax, (7.0, 2.4), 1.1, 1.1, "$S_4$", "$4 \\times 4$", "4 singular values", ORANGE)
    block(ax, (10.8, 2.4), 2.0, 0.95, "$V_4^\\top$", "$4 \\times 10$", "4 asset directions", TEAL)
    block(ax, (14.8, 2.4), 1.3, 2.5, "$X_4$", "$750 \\times 10$", "Rank ≤ 4 estimate", BLUE)
    for x, symbol in ((2.6, "$\\approx$"), (5.5, "$\\times$"), (8.7, "$\\times$"), (13.0, "$=$")):
        ax.text(x, 2.4, symbol, ha="center", va="center", fontsize=27, color=INK)
    fig.suptitle(
        "Truncated SVD: keep a few directions, approximate the matrix",
        fontsize=17,
        color=INK,
        y=0.99,
    )
    fig.text(
        0.5,
        0.055,
        r"$X_k=U_k S_k V_k^\top$ is exact; $X \approx X_k$ discards the omitted modes.",
        ha="center",
        fontsize=12,
        color=INK,
    )
    fig.text(
        0.5,
        0.005,
        "k = 4 is a teaching example. The portfolio experiment fixes k = 3.",
        ha="center",
        fontsize=10,
        color="#526477",
    )
    save(fig, "picture2")


def variance_figure():
    prices, audit = load_prices(UNIVERSES["us_equity"], ResearchConfig(), ROOT)
    tickers = [ticker for ticker in UNIVERSES["us_equity"].tickers if ticker != "XLRE"]
    window = prices.loc["2021-09-01":"2024-08-31", tickers]
    returns = simple_returns(window)
    centered = returns - returns.mean()
    _, singular_values, _ = np.linalg.svd(centered.to_numpy(), full_matrices=False)
    shares = singular_values**2 / np.sum(singular_values**2)
    components = np.arange(1, len(shares) + 1)
    table = pd.DataFrame(
        {
            "component": components,
            "singular_value": singular_values,
            "covariance_eigenvalue": singular_values**2 / (len(centered) - 1),
            "variance_share": shares,
            "cumulative_variance_share": shares.cumsum(),
        }
    )
    table.to_csv(DESTINATION / "variance_explained.csv", index=False, float_format="%.12g")
    fig, ax = plt.subplots(figsize=(10, 5.3), layout="constrained")
    ax.bar(components, shares, width=0.65, color="#3478bf", label="Individual component")
    ax.plot(components, shares.cumsum(), "o-", color="#008575", label="Cumulative share", lw=2)
    ax.annotate(
        f"PC1: {shares[0]:.1%}",
        (1, shares[0]),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=11,
        color=INK,
    )
    ax.annotate(
        f"First three: {shares[:3].sum():.1%}",
        (3, shares[:3].sum()),
        xytext=(10, -28),
        textcoords="offset points",
        ha="left",
        fontsize=11,
        color=INK,
    )
    ax.set(
        title="How much return variation does each principal component explain?",
        xlabel="Principal component (largest variance first)",
        ylabel="Share of total sample variance",
        xticks=components,
        ylim=(0, 1.07),
    )
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)
    ax.legend(loc="center right", frameon=False)
    fig.text(
        0.5,
        -0.065,
        f"Original 10-sector universe • {len(returns)} centered daily returns • "
        f"{returns.index[0]:%Y-%m-%d}–{returns.index[-1]:%Y-%m-%d}\n"
        "Yahoo Finance adjusted-close snapshots; descriptive PCA, not a trading backtest.",
        ha="center",
        fontsize=9,
        color="#526477",
    )
    save(fig, "usequity_var_explained")
    return {
        "purpose": "Descriptive centered PCA using the original post's 10-ETF universe and dates",
        "tickers": tickers,
        "return_rows": len(returns),
        "first_return": str(returns.index[0].date()),
        "last_return": str(returns.index[-1].date()),
        "centering": "Column means estimated over this descriptive window",
        "standardization": "None; covariance-space PCA",
        "pc1_variance_share": float(shares[0]),
        "first_three_share": float(shares[:3].sum()),
        "snapshots": [item for item in audit["snapshots"] if item["ticker"] in tickers],
    }


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "svg.fonttype": "none", "font.family": "DejaVu Sans"})
    diagrams()
    variance = variance_figure()
    exported = []
    for universe, figure in (
        ("us_equity", "volatility_intervals"),
        ("us_equity", "sensitivity"),
        ("multi_asset", "weights"),
    ):
        source = ROOT / "outputs" / universe
        verify_manifest(ROOT, universe)
        for extension in ("png", "svg"):
            source_figure = source / "figures" / f"{figure}.{extension}"
            destination = DESTINATION / f"{universe}_{figure}.{extension}"
            shutil.copyfile(source_figure, destination)
            exported.append(
                {
                    "file": destination.name,
                    "source": str(source_figure.relative_to(ROOT)),
                    "sha256": sha256(destination),
                    "research_manifest_sha256": sha256(source / "manifest.json"),
                }
            )
    # Matplotlib path data may include trailing spaces; keep generated diffs clean.
    for path in DESTINATION.glob("*.svg"):
        path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    for entry in exported:
        entry["sha256"] = sha256(DESTINATION / entry["file"])
    provenance = {
        "generator": "scripts/build_article_assets.py",
        "generator_sha256": sha256(Path(__file__)),
        "original_blog_images": [
            {"file": str(path.relative_to(DESTINATION)), "sha256": sha256(path)}
            for path in sorted((DESTINATION / "originals").glob("*.png"))
        ],
        "variance_illustration": variance,
        "research_figures": exported,
        "publication_files": {
            path.name: sha256(path)
            for path in sorted(DESTINATION.iterdir())
            if path.suffix in (".png", ".svg", ".csv")
        },
    }
    (DESTINATION / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Created publication figures in {DESTINATION}")
    print(
        f"Centered PC1 share: {variance['pc1_variance_share']:.4%}; "
        f"first three: {variance['first_three_share']:.4%}"
    )


if __name__ == "__main__":
    main()
