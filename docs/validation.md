# Validation record

The revised studies use downloaded ETF prices. Synthetic returns appear only in the unit tests.

- `uv run pytest -q`: 16 tests passed. The tests cover information timing, future-data
  perturbations, ticker-order invariance, a known minimum-variance solution, residual risk,
  positive semidefiniteness, trading costs, drift, initial drawdown, calendar boundaries,
  missing-data rejection, paired bootstrap reproducibility and rejection of changed raw snapshots.
- `uv run ruff check src scripts tests` and `uv run ruff format --check src scripts tests`:
  both passed on the delivered code.
- Both notebooks executed in fresh project-environment kernels: 12 executed code cells and
  six saved figures per notebook, with no cell errors. HTML exports contain the five expected
  tables and the complete narrative section order.
- All twelve rendered figures were visually inspected. The covariance-comparison confidence
  intervals use a separately labeled expanded scale so small effects remain visible.
- For both universes, all 1,527 evaluated daily gross returns were independently reconciled
  from saved pre-return holdings and raw asset returns. Net returns reconcile with the saved
  fees; every target satisfies the budget and concentration constraints.
- The first PCA common-portfolio variance forecast was cross-checked by reconstructing the
  sample-covariance eigenvectors with an eigensolver, independently of the SVD implementation.
- Data checks found 2,052 price rows per ETF, complete expected NYSE sessions and no missing
  prices. No absolute daily return exceeded the declared 25% review threshold.
- The results writer checks result-file hashes, the shared source-code fingerprint and the
  dependency-lock fingerprint and the actual cached raw vintage before regenerating the summary, blog result table or publication figures.

The PNG figures and notebook output text were inspected directly; the exported HTML structure
was checked programmatically. A full browser-level HTML layout inspection was unavailable in
this environment. Open `outputs/SVD-US_Equity.html` and `outputs/SVD-Multi_Asset.html` in a browser
to check presentation in the intended publishing context. No live blog publication was performed.

The installed pandas/NumPy combination emits non-fatal timedelta deprecation warnings. The
recorded tests and notebook runs complete successfully with the locked environment.

The initial workspace had no Git metadata. The original source snapshot is now preserved on
`old` at `4d76751d16966aefa8ffce184f5f2ed917e6e24b` under the user's explicit backup request. No pre-existing history was reconstructed.

Renovation verification on 19 September 2026 also ran `uv sync --locked --offline`,
`scripts/check_artifacts.py` (1,527 sessions, five strategies and 73 rebalances per universe),
`scripts/export_evidence.py` and `scripts/check_publication.py`. Independent results are saved
in `research/results/independent_validation.json`. Both notebooks were re-executed; article
assets and the local publication bundle were regenerated. GitHub CI was configured but not
run remotely. The compact evidence register excludes raw histories and detailed daily paths.
