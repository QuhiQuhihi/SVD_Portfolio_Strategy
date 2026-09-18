# SVD renovation audit — 19 September 2026

The starting directory had no Git metadata. The user requested original-version preservation
on `old` for all four named projects and reaffirmed SVD's inclusion. The original source tree
is now local commit `4d76751d16966aefa8ffce184f5f2ed917e6e24b`, preserved on `old`; work proceeds on `renovation`.
An additional local tar recovery snapshot was created before any source edit. Raw downloads,
environments and ignored generated paths are excluded from the Git snapshot.

Read: README, both maintained notebooks as JSON, canonical article, protocol, review,
results/validation/publishing records, source modules, scripts, tests and source metadata.
The main teaching figures were visually inspected and retained. Corporate-bond reference:
`1f565f6d7010274ff8feb333b9c05be11ba1dcfa`, including protocol, sources, evaluation and publication.

The existing revision already fixed the original uncentered/full-sample SVD and unrealistic
singular-value leverage. Those historical issues and exact cells remain documented in
[research_review](../docs/research_review.md); originals remain in `archive/` and on `old`.
This renovation preserves the educational derivation and both empirical universes.

## Verified current defects and repairs

- `.venv/bin/pytest` and other installed scripts retained a previous checkout's absolute
  shebang. `uv run pytest` failed before executing; `uv run python -m pytest` passed all 15
  existing tests. Reinstalling the exact lock repaired the relocatable Linux environment.
- `scripts/write_results.py` verified code, lock and output tables but did not compare current
  raw snapshot files/metadata against the run's source vintage. A source could change while
  the presentation command still accepted old results. `verify_manifest` now rejects that
  condition; a changed-price regression test covers it.
- The results writer hard-coded sample dates/counts and interpretation statements. These are
  now derived from verified artifacts, with an explicit shared-sample check across universes.
- Independent accounting checks existed only as a prose assurance. A maintained command now
  reconstructs all gross/net daily returns, rebalance fees and turnover, headline metrics and
  an initial PCA risk forecast using a separate covariance eigensolver.
- No CI or compact versioned source/result register was present. These now accompany the
  existing pipeline; CI's offline/synthetic scope is explicit.

## Disposition and scope

Retain source model/timing logic after tests and independent accounting checks. Retain original
and corrected conceptual figures. Re-execute both maintained notebooks. Repair results writing,
add provenance/accounting validation, source register, evidence exports and CI. Keep the complete
month-end August 2026 sample fixed: the task does not require retuning an already executed SVD
experiment when refreshing the two other projects. The September extension is not silently
mixed into this comparison. No new strategy, alpha claim or independent holdout is asserted.

The primary question remains whether a PCA factor-plus-diagonal covariance improves constrained
risk allocation versus shrinkage. Surviving ETF selection, revised data, zero cash benchmark,
short late period and bond-heavy multi-asset exposures limit interpretation.
