# Renovation acceptance evidence

19 September 2026: the established two-notebook layout is retained per [protocol mapping](PROTOCOL.md).

| Scope | Evidence |
|---|---|
| Original preservation and audited changes | `old` at `4d76751`; additional original local tar; [audit](AUDIT.md) and existing [research review](../docs/research_review.md). |
| Inputs/design | [Source register](SOURCES.md), exact [input manifest](data/input_manifest.json), original August-end sample and [protocol](../docs/research_protocol.md). |
| Numerical execution and inference | Both freshly executed notebooks, [generated results](../docs/results_summary.md), pointwise dependence-aware intervals and all declared sensitivities. |
| Independent correctness | 16 passing tests; [independent reconciliation](results/independent_validation.json) covers holdings, fees, budget/cap/timing, headline metrics and separate PCA eigensolver. |
| Provenance defect repaired | Writers/exporters verify the actual raw snapshot vintage against the executed run; changed-price regression test passes. |
| Reproducibility | Locked offline environment, lint/format, executed notebooks, artifact and public checks pass; exact commands in [work log](WORKLOG.md). |
| Teaching and figures | Existing coherent SVD/PCA explanation preserved; 12 empirical figures and mathematical/scree illustrations visually reviewed. |
| Publication | Relative links and embedded notebook outputs valid, tracked compact evidence, local Jekyll bundle generated; no remote workflow or publication. [Rights/history boundary](../PUBLICATION.md). |
| Conclusion and future work | Small sample-specific volatility differences do not establish general forecasting superiority or alpha; [next experiment](RESEARCH_AGENDA.md) is unrun. |

Exact full reproduction requires the permitted pinned cache. CI does not download raw histories.
Future-vintage evaluation, second-vendor reconciliation and live execution remain outside this
verification revision; they are not represented as completed research.
