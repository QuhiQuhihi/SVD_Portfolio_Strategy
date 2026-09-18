# Validation record

The revised studies use downloaded ETF prices. Synthetic returns appear only in the unit tests.

- `uv run pytest -q`: 15 tests passed. The tests cover information timing, future-data
  perturbations, ticker-order invariance, a known minimum-variance solution, residual risk,
  positive semidefiniteness, trading costs, drift, initial drawdown, calendar boundaries,
  missing-data rejection and paired bootstrap reproducibility.
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
  dependency-lock fingerprint before regenerating the summary and blog result table.

The PNG figures and notebook output text were inspected directly; the exported HTML structure
was checked programmatically. A full browser-level HTML layout inspection was unavailable in
this environment. Open `outputs/SVD-US_Equity.html` and `outputs/SVD-Multi_Asset.html` in a browser
to check presentation in the intended publishing context. No live blog publication was performed.

The installed pandas/NumPy combination emits non-fatal timedelta deprecation warnings. The
recorded tests and notebook runs complete successfully with the locked environment.

The workspace did not contain usable Git metadata, so no commit was created. Original notebooks
were copied unchanged to `archive/` before revision; dependencies and the lockfile are included
for version control when this work is placed in a Git checkout.
