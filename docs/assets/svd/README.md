# Article figures and provenance

These publication assets are included in the repository. They are intentionally outside the
ignored `outputs/` directory so Markdown images work on public GitHub without executing a notebook.

## The three concept figures

| File | Role | Changes from the original post |
|---|---|---|
| `picture1.png` | Full SVD and the dimensions of its factors | New vector schematic with readable labels, centered-return notation, and a note distinguishing reduced SVD |
| `picture2.png` | Truncated reconstruction | New vector schematic with `X ≈ U₄S₄V₄ᵀ = X₄`, retained dimensions, and an explicit rank bound |
| `usequity_var_explained.png` | Individual and cumulative explained variance | Recomputed on centered returns; components numbered 1–10; dates, universe, and cumulative shares shown |

The mathematical diagrams retain the original teaching example of 750 observations and ten
assets. These are illustrative dimensions, not a claim about the exact number of observations
in the ETF sample. The truncation diagram uses four components to explain the multiplication;
the allocation experiment fixes three.

The original `picture1.png`, `picture2.png`, and `usequity_var_explained.png` were copied unchanged
from the author's blog assets into [originals/](originals/). The new diagrams are generated from
mathematical dimensions as vector figures; the original raster images are not edited.

## Explained-variance calculation

The replacement scree plot uses the original ten-sector universe, excluding XLRE, and the
original September 2021–August 2024 price window. It uses current-vintage cached Yahoo Finance
adjusted closes from the revised research project, rather than claiming to reproduce the exact
2024 download. The first undefined return is dropped and column means are subtracted.

- 753 daily returns: September 2, 2021–August 30, 2024.
- Covariance-space PCA: centered, without volatility standardization.
- PC1 variance share: 61.7151%; first three components: 85.4518%.
- Inspectable plotting data: [variance_explained.csv](variance_explained.csv).
- Input tickers, snapshot hashes, retrieval timestamps and artifact hashes:
  [provenance.json](provenance.json).

This is a descriptive explanation of PCA, independent of the walk-forward strategy. The
current sector backtest adds XLRE, uses rolling 504-session windows, and begins portfolio
evaluation in August 2020. The full descriptive sample's loadings are never used to trade
earlier backtest dates.

## Research figures

`us_equity_volatility_intervals`, `us_equity_sensitivity`, and `multi_asset_weights` are copied
from the executed notebook outputs. Their source paths and hashes are recorded in the provenance
file. Their definitions and dates are given in the article captions and research protocol.

All six figures have both PNG and SVG versions. The Markdown uses PNGs for consistent rendering;
the SVGs preserve vector geometry for resizing and export. Regenerate using:

```bash
uv run python scripts/build_article_assets.py
```

This command requires validated local price snapshots and the executed research outputs. It
does not download prices. If the research code or data have changed, rerun the notebooks first.
