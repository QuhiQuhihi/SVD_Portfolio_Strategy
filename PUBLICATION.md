# Publication review

Use [the existing publishing guide](docs/PUBLISHING.md) for the local Jekyll bundle. The original
source snapshot is preserved on `old`; reviewed changes are on `renovation`. No remote push or
live site change is authorized or performed by this renovation.

Before release, run `uv run python scripts/check_artifacts.py`,
`uv run python scripts/check_publication.py`, and the README reproduction commands. The first
checks cached raw vintages, independent holdings accounting and headline statistics; the second
checks public links, notebook outputs and source/evidence-register presence without downloads.

Raw Yahoo histories, generated daily paths, environments and caches remain ignored. The compact
summary CSVs and original/updated illustrations are included for inspection. Provider and
original-author rights still apply; no unrestricted redistribution or commercial license is
inferred. The `old` snapshot and legacy notebooks are recovery material, not a fresh rights
clearance. Rendered PNGs and saved notebook outputs are inspected locally; a live Jekyll/browser
publication check remains a separate task.

CI installs the exact lock, runs unit tests, lint/format checks and public-file checks. It does
not fetch licensed data or reproduce the complete historical study. Full offline research uses
the cached inputs and commands recorded in `research/WORKLOG.md`.
