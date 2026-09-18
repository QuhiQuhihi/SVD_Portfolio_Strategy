# Publish the educational article and research code

The README is the public repository introduction. `docs/blog_draft.md` is the longer article,
with Jekyll front matter, equations, executable examples, and relative image links for GitHub.
The title now introduces SVD/PCA and systematic investing; the portfolio experiment is the
worked application within that teaching sequence.

## GitHub

Include the README, `docs/` (including `docs/assets/svd/`), the two executed notebooks, `src/`,
`scripts/`, `tests/`, `pyproject.toml`, `uv.lock`, `.python-version`, and `.gitignore`. Retain the
existing repository license when applying these files to your checkout. The original notebooks
and original teaching images remain available for comparison.

The README and draft reference tracked publication figures, so they render without raw price
data or `outputs/`. Do not point public Markdown at local Windows paths or ignored generated
directories. Review the local `renovation` branch against `old`. The latter preserves the starting source
snapshot; prior Git history was unavailable. Push and publication remain separate actions.

## Prepare the Jekyll post

From the project root:

```bash
uv run python scripts/build_article_assets.py
uv run python scripts/prepare_blog.py
```

The asset command uses existing data and results; the preparation command only checks and
copies files. Neither command publishes or modifies the separate blog checkout.

The prepared bundle is under `outputs/blog_publication/`:

```text
_posts/ML/2024-09-25-SVD_and_Portfolio.md
assets/img/post_image/ML/SVD/
    picture1.png
    picture2.png
    usequity_var_explained.png
    us_equity_volatility_intervals.png
    us_equity_sensitivity.png
    multi_asset_weights.png
    ... matching SVG files
manifest.json
```

The post keeps the original filename and publication date, and adds the revision date. Its
metadata retains math support and the `ML in Finance` category. The author name is the public
GitHub handle `QuhiQuhihi`; adjust it to your site's preferred byline if needed.

The preparation script converts relative figure paths to your existing
`/assets/img/post_image/ML/SVD/` URL convention. Notebook and supporting-document links point to
the research repository's `main` branch. Those new files should be available on GitHub before
publishing the blog revision.

## Apply the bundle to the blog checkout

Review the prepared Markdown and six figures, then copy the bundle's `_posts/` and `assets/`
contents into the corresponding directories in `C:\workspace\QuhiQuhihi.github.io`
(`/mnt/c/workspace/QuhiQuhihi.github.io` in WSL). This replaces the existing post and the three
same-named concept images; their original copies are preserved in this project's asset archive.
Do not replace the entire surrounding directories, which contain other posts and assets.

Use the blog repository's normal local Jekyll preview to check equations, image widths, code
formatting, and the article's URL before committing the revision. The figures were visually
inspected and the article's Python examples executed here; the separate blog's full Jekyll
build was not run in this environment.

## Updating results later

After rerunning the research notebooks, regenerate the evidence and publication assets:

```bash
uv run python scripts/write_results.py
uv run python scripts/build_article_assets.py
uv run python scripts/prepare_blog.py
```

`write_results.py` updates the marked results block in the draft while preserving the surrounding
tutorial. It does not rewrite narrative figures, dates, interpretations, or numerical examples
elsewhere in the text. Review those sentences against the new results when refreshing the data
or changing the research specification.
