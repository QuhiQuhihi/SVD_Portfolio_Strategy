# Instructions for Research and Technical Blog Projects

## Purpose and scope

Help develop research projects that are both educational and technically credible. The
repository should let a reader understand the main ideas, inspect the evidence, reproduce
the analysis, and assess its limitations. Strong reasoning and honest conclusions matter
more than impressive performance or complicated methods.

These instructions are reusable across research topics. Adapt the project context section
at the end when copying this file to another repository. Apply domain-specific requirements
only when relevant; do not impose a finance workflow on an unrelated topic.

Follow the user's current request and preserve their intended audience and teaching goals.
An improvement request authorizes useful work within its scope; it does not require replacing
an entire project or adding every possible experiment. Treat suggestions for future research
as proposals unless the user has asked to implement them.

## Before making changes

- Read the README, relevant source code, existing article or notebook, and applicable local
  instructions. Read supplied blog sources and inspect important figures before revising them.
- Identify the research question, intended audience, main concepts to teach, available data,
  existing results, and requested deliverables.
- Inspect Git status and existing changes. Preserve unrelated work. If Git metadata is
  unavailable, say so; do not initialize a repository or claim to have reviewed a Git diff.
- Distinguish material already supported by executed analysis from hypotheses, illustrations,
  and proposed extensions. Never assume an existing chart or conclusion is correct.
- Ask concise questions when missing information materially affects correctness or scope.
  Continue independent work while awaiting answers, and state reasonable assumptions.
- Before lengthy downloads or computations, identify output paths, expected overwrite effects,
  and the restart or recovery procedure. Reuse valid intermediate artifacts when possible.

## Research design

Frame the work around a specific, testable question. Explain why the question matters, the
mechanism being investigated, what is measured, and what evidence would contradict the claim.
The title should describe the subject and actual contribution without promising an outcome.

For empirical work, as applicable:

- Define the sample, unit of observation, inclusion rules, time range, transformations, and
  evaluation metrics. State important assumptions before interpreting the results.
- Include simple baselines and relevant established alternatives. Use comparable data,
  constraints, evaluation periods, and resource assumptions across methods.
- Separate fitting, model selection, and evaluation. Respect temporal or grouped dependence.
  Fit preprocessing only on the appropriate training data; check for information leakage.
- Label exploratory, retrospective, and genuinely prospective evaluations accurately.
  A historical split does not erase earlier exposure to the data or results.
- Evaluate effect sizes, uncertainty, sensitivity, and practical significance. Choose
  uncertainty methods appropriate to dependence and sampling; explain what they omit.
- Show unfavorable results and reasonable robustness checks. Do not tune a primary method
  on the evaluation set, hide reversals, or present repeated variants as independent evidence.
- Separate association, prediction, and causation. Use causal language only when the design
  supports it. Keep the strength of the conclusion proportional to the evidence.

For mathematical or simulation projects, state assumptions, derive the relevant relationships,
check dimensions and limiting cases, and distinguish proofs from numerical illustrations.
Do not invent an empirical experiment when the question is better answered analytically.

## Data and provenance

- Record source URLs or identifiers, retrieval dates, sample coverage, units, and relevant
  usage restrictions. Preserve snapshot hashes or version identifiers where practical.
- Validate schema, missingness, duplicates, alignment, ordering, units, and unexpected values.
  Document exclusions and cleaning. Do not silently fill, clip, or drop observations.
- Separate raw inputs from derived data and outputs. Avoid replacing a valid source snapshot
  merely to rerun code; document when refreshing it changes the data vintage.
- Label synthetic and illustrative data clearly. Never present simulated values as observations.
- Keep credentials, secrets, personal information, environments, and caches out of version
  control. Check whether source data may be redistributed before including them publicly.

## Code and reproducibility

- Run development commands in WSL Ubuntu as Linux user `daham`. The usual workspace root is
  `/mnt/c/workspace`, corresponding to `C:/workspace` on Windows.
- Use Linux-native Python, Git, uv, Node, and build tools. Do not reuse Windows virtual
  environments or Windows `node_modules`, or edit the checkout concurrently from Windows.
- For Python projects, prefer `pyproject.toml`, `uv.lock`, and `uv sync --locked` / `uv run`.
  Use `uv add` and `uv remove` for dependency changes and retain the lockfile for version control.
- Keep reusable analytical logic in modules. Use notebooks for explanation, exploration, and
  inspection of results. Avoid maintaining divergent copies of the same method.
- Use explicit configuration and reproducible seeds where relevant. Validate inputs and
  optimization outcomes; do not silently substitute a fallback that changes the experiment.
- Use portable project-relative paths in code and public documents. Keep machine-specific
  source locations in a clearly identified local context section.
- Generate result tables and quantitative figures from the analysis. Preserve the connection
  between data, configuration, code, dependencies, and outputs.
- Do not bypass stale-output or provenance checks by editing hashes. Rerun the affected
  analysis or report that the evidence cannot currently be regenerated.

## Writing and mathematical explanation

The README should explain the purpose, main question, important concepts, repository layout,
reproduction steps, supported findings, and limits. The blog draft should develop the ideas
as a coherent article rather than reproduce a code listing or a project changelog.

- Start with a motivating problem, build intuition, define notation and assumptions, then
  introduce the mathematics, implementation, evidence, and interpretation.
- Define symbols, matrix dimensions, units, and conventions before relying on them. Distinguish
  exact identities, approximations, estimators, and assumptions.
- Connect each technique to a concrete use. Separate implemented applications from potential
  extensions; explaining a possible application does not establish that it works.
- Include small executable examples when they help readers connect equations to code.
- Cite primary papers, official documentation, and original data sources near the relevant
  claims. Verify supplied references and unfamiliar or changing technical facts.
- Use clear, professional prose and informative headings. Avoid inflated claims, promotional
  language, and jargon that adds no precision.
- Check every reported number, date, caption, and interpretation against the current evidence.
  Regenerating a table does not automatically update surrounding prose.
- Preserve the educational purpose when strengthening the research. A more sophisticated
  experiment should not remove the explanation that helps a reader understand the method.

## Figures and assets

- Inspect supplied figures and preserve meaningful originals before replacing them.
- Generate quantitative plots and mathematical diagrams from code using suitable plotting
  or vector tools. Do not use illustrative image generation to fabricate empirical charts.
- Check labels, units, dimensions, scales, legends, sample periods, readability, and captions.
  Distinguish schematic figures from measured results and training diagnostics from evaluation.
- Save publication assets in a version-controlled location. Public Markdown should not depend
  on ignored output folders, local absolute paths, or access to raw datasets.
- Keep plotting inputs and provenance available. Prefer PNG for straightforward embedding and
  SVG or PDF when scalable export is useful.

## Validation proportional to the change

- For analytical code changes, run relevant tests and applicable lint/format checks. Add tests
  for meaningful mathematical, data, timing, or accounting invariants and identified bugs.
- For notebook changes, execute affected notebooks from a clean kernel when feasible. Preserve
  the last successful artifact until execution completes; inspect tables and rendered figures.
- For prose-only changes, verify claims, equations, references, and links. Run changed code
  examples. Do not rerun expensive experiments or add tests merely to validate wording.
- For figure changes, regenerate affected assets, inspect their appearance, and reconcile
  plotted values with their source data.
- For method, data, or configuration changes, regenerate affected downstream results and
  publication assets. Review narrative conclusions as well as generated tables.
- Report which checks actually ran, their results, and material checks that remain unavailable.
  Never describe an unexecuted notebook or unbuilt site as validated.

## Publication and collaboration

Keep publication preparation separate from live publication. Prepare reviewable local artifacts
within the requested scope. Follow existing authorization for commits, pushes, external edits,
or publishing; do not infer permission to publish from a statement that the user will publish.
Do not ask again for an action the user has already authorized.

Preserve existing article URLs, front matter, attribution, license, and asset conventions unless
a change is needed. Check public links, image rendering, equations, and code formatting in the
intended publishing context when that environment is available.

Give concise progress updates during substantial work. Finish with the files changed, the
reason for material changes, validation performed, and any actual limitation. Do not invent
approval requirements or modify unrelated infrastructure. Never change SSH, Tailscale,
firewall, power, Task Scheduler, WSL settings, or security controls without an explicit request.

## Project context: SVD and PCA for Systematic Investing

This section is specific to this repository. Replace it for a different research topic.

**Purpose:** teach SVD and PCA, then assess a concrete systematic investing application:
PCA covariance estimation for constrained portfolio risk allocation. Preserve both the
conceptual explanation and the empirical evaluation. Explained variance does not establish
predictive ability, alpha, or improved portfolio performance.

**Read first:**

- `README.md`: public introduction and reproduction instructions.
- `docs/blog_draft.md`: canonical article draft.
- `docs/research_protocol.md`: research design, estimators, timing, costs, and metric definitions.
- `docs/research_review.md`, `docs/results_summary.md`, and `docs/validation.md`: methodological
  context, generated evidence, and the recorded scope of validation.
- `docs/PUBLISHING.md`: asset generation and Jekyll handoff.

**Implementation:** reusable code is in `src/svd_portfolio/`; configuration is in `config.py`.
The executable companions are `SVD-US_Equity.ipynb` and `SVD-Multi_Asset.ipynb`. Tests are in
`tests/`; original notebooks are preserved in `archive/`. Keep changes consistent with the
protocol, including training-only fitting, execution delay, drifting holdings, and trading costs.

**Assets:** `docs/assets/svd/` contains publication figures and provenance. Preserve its
`originals/` directory. The key teaching figures are `picture1.png`, `picture2.png`, and
`usequity_var_explained.png`. Keep full, reduced, and truncated SVD distinct; use squared
singular values for explained variance of centered returns. The historical ten-sector teaching
example and the current eleven-sector backtest have different purposes and samples.

**Commands:** select the steps needed for the requested change; this is not a mandatory full
rerun for every edit.

```bash
uv sync --locked
uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests

# Use existing cached data for research; add --download only when snapshots are missing.
uv run python scripts/run_research.py --sensitivity
uv run python scripts/execute_notebooks.py
uv run python scripts/write_results.py
uv run python scripts/build_article_assets.py
uv run python scripts/prepare_blog.py
```

Downloads checkpoint by ticker in `data/raw/`; rerunning with `--download` resumes missing
snapshots. `--refresh --download` deliberately replaces the data vintage. Generated research
outputs are in `outputs/<universe>/`; the prepared site bundle is in `outputs/blog_publication/`.
These directories are ignored by Git. When dependencies and data are already present,
`UV_CACHE_DIR=/tmp/svd-uv-cache uv run --offline ...` supports restricted environments.

`scripts/build_notebooks.py` rebuilds notebook content and clears outputs: use it only when
changing the shared notebook template, then execute the notebooks. `write_results.py` updates
the article's `RESULTS:START` / `RESULTS:END` block; review quantitative prose outside that block
manually. Do not edit generated summaries as a substitute for correcting their source.

**Original blog references:**

- Public article: https://quhiquhihi.github.io/posts/SVD_and_Portfolio/
- Local source: `/mnt/c/workspace/QuhiQuhihi.github.io/_posts/ML/2024-09-25-SVD_and_Portfolio.md`
- Local original figures: `/mnt/c/workspace/QuhiQuhihi.github.io/assets/img/post_image/ML/SVD/`

Use these as references. Routine preparation writes to this repository's local publication
bundle; editing the separate blog checkout or publishing requires task authorization. Check
current Git and build availability rather than assuming earlier environment limitations persist.
