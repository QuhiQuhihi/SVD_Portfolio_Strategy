# Protocol mapping and renovation amendment

The maintained numerical design is [docs/research_protocol.md](../docs/research_protocol.md).
It remains unchanged: 504 trailing sessions, three factors, 30% cap, monthly delayed close
execution, five-basis-point bought/sold-dollar costs, fixed universes and January 2025–August
2026 retrospective evaluation. This file maps the renovation brief to the established layout.

19 September 2026 amendment: verification and publication tooling only. Add raw-vintage checks,
independent saved-path accounting/eigensolver validation, generated sample metadata and CI.
No strategy selection, source refresh or primary endpoint change. Both notebooks are regenerated
from the original hashed August-end snapshots; conclusions must agree with that evidence.

Deliverable mapping: `study.ipynb` corresponds to the two complementary maintained notebooks
`SVD-US_Equity.ipynb` and `SVD-Multi_Asset.ipynb`; a redundant third analysis is not maintained.
Narrative lives in `README.md`, `docs/blog_draft.md` and `docs/results_summary.md`. Reusable
calculations remain in `src/svd_portfolio/`, orchestration in `scripts/`. Publication figures
are in `docs/assets/svd/`, source metadata and compact summary evidence in `research/`.
