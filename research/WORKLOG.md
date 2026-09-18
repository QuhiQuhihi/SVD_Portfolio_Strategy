# Recovery and handoff

Original local snapshot `4d76751d16966aefa8ffce184f5f2ed917e6e24b` on `old`; renovation on `renovation`. No original Git history
was available; this snapshot does not invent or restore it. Additional original tar archive is
outside the checkout in the workspace's `.renovation_backups/`.

Preserved all original sources and figures. Locked environment reinstalled to repair moved
absolute script paths. Initial 15 tests passed via Python. New raw-vintage regression test and
independent artifact checker added. Original August-end source vintage retained.

Outputs: `outputs/<universe>/` (ignored detailed paths), `research/results/` (compact evidence),
`docs/assets/svd/` (publication figures), the two executed notebooks and local HTML previews.
Recovery from immutable cache: `uv sync --locked`; `uv run python scripts/execute_notebooks.py`;
`uv run python scripts/check_artifacts.py`; `uv run python scripts/write_results.py`;
`uv run python scripts/build_article_assets.py`; `uv run python scripts/prepare_blog.py`;
`uv run python scripts/export_evidence.py`. Notebook files replace originals only after success.

If a moved environment still has stale shebangs: `uv sync --locked --reinstall`; environments
are excluded from version control. Verification outcomes follow below.

## Completed verification — 19 September 2026 KST

- `uv sync --locked --offline`: passed; relocated Linux script entry points repaired earlier with exact-lock reinstall.
- `uv run python -m pytest -q`: **16 passed**, five non-fatal dependency deprecation warnings.
- `uv run python -m ruff check src scripts tests` and `uv run python -m ruff format --check src scripts tests`: passed.
- `uv run python scripts/execute_notebooks.py`: both notebooks completed in fresh kernels; 12 code cells and six embedded figures each, zero errors. Local HTML previews contain five tables each.
- `uv run python scripts/check_artifacts.py`: all five strategies, 1,527 sessions and 73 rebalances per universe independently reconciled; first PCA forecast matched a separate eigensolver calculation.
- `uv run python scripts/write_results.py`: refreshed narrative from verified raw vintage and artifacts, including actual dates, sample sizes, configuration and interval interpretation.
- `uv run python scripts/build_article_assets.py` and `uv run python scripts/prepare_blog.py`: generated verified figures and local Jekyll handoff, preserving the original post path and attribution. SVG trailing whitespace normalized; numerical plots unchanged.
- `uv run python scripts/export_evidence.py`: exported aggregate evidence and manifests to `research/results/`.
- `uv run python scripts/check_publication.py`: relative links, notebooks and source/evidence registers passed.
- Twelve empirical PNGs and the full/reduced/truncated SVD and centered scree illustrations inspected; original figures retained. HTML structure checked programmatically; no full browser/site build certification.

Both original August-end universes and primary specifications remain unchanged. No remote push,
GitHub workflow run or live publication occurred. Numerical limits remain documented in
[results](../docs/results_summary.md) and [publication review](../PUBLICATION.md).

Final Git review: original `old` reference verified; maintained Markdown links resolve within the staged tree. Tracked evidence hashes match staged bytes, and raw/recovery/environment paths are absent. `.gitattributes` preserves Linux source line endings and exact hashed CSV serializer bytes. Staged whitespace checks pass.
