"""Prepare a local Jekyll post bundle; does not modify a blog checkout or publish anything."""

import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit

from svd_portfolio.data import sha256

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets" / "svd"
DESTINATION = ROOT / "outputs" / "blog_publication"
BLOG_ASSETS = "assets/img/post_image/ML/SVD"
POST_PATH = "_posts/ML/2024-09-25-SVD_and_Portfolio.md"
REPOSITORY = "https://github.com/QuhiQuhihi/SVD_Portfolio_Strategy/blob/main/"


def main():
    draft = ROOT / "docs" / "blog_draft.md"
    content = draft.read_text()
    if not content.startswith("---\n") or "math: true" not in content:
        raise ValueError("Blog draft needs Jekyll front matter and math enabled")
    provenance = json.loads((ASSETS / "provenance.json").read_text())
    if provenance["generator_sha256"] != sha256(ROOT / provenance["generator"]):
        raise ValueError("Asset generator changed; run scripts/build_article_assets.py")
    for name, expected in provenance["publication_files"].items():
        if sha256(ASSETS / name) != expected:
            raise ValueError(f"Publication asset hash mismatch: {name}")
    referenced_images = set()

    def rewrite(match):
        image_marker, label, target = match.groups()
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith("#"):
            return match.group(0)
        source = (draft.parent / parsed.path).resolve()
        if not source.is_relative_to(ROOT) or not source.exists():
            raise ValueError(f"Unresolved local Markdown target: {target}")
        if image_marker:
            if source.parent != ASSETS:
                raise ValueError(f"Publish images from the tracked asset directory: {target}")
            referenced_images.add(source.name)
            destination = f"/{BLOG_ASSETS}/{source.name}"
        else:
            destination = REPOSITORY + quote(str(source.relative_to(ROOT)), safe="/")
            if parsed.fragment:
                destination += "#" + parsed.fragment
        return f"{image_marker}[{label}]({destination})"

    content = re.sub(r"(!?)\[([^\]]+)\]\(([^)]+)\)", rewrite, content)
    post = DESTINATION / POST_PATH
    post.parent.mkdir(parents=True, exist_ok=True)
    destination_assets = DESTINATION / BLOG_ASSETS
    destination_assets.mkdir(parents=True, exist_ok=True)
    for name in sorted(referenced_images):
        shutil.copyfile(ASSETS / name, destination_assets / name)
        svg = (ASSETS / name).with_suffix(".svg")
        if svg.exists():
            shutil.copyfile(svg, destination_assets / svg.name)
    post.write_text(content)
    files = [
        post,
        *sorted(destination_assets.glob("*.png")),
        *sorted(destination_assets.glob("*.svg")),
    ]
    (DESTINATION / "manifest.json").write_text(
        json.dumps(
            {
                "source_draft": "docs/blog_draft.md",
                "source_sha256": sha256(draft),
                "files": {str(path.relative_to(DESTINATION)): sha256(path) for path in files},
                "status": "Prepared locally; no changes to the blog checkout and no publication",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Prepared {post}")
    print(f"Bundled {len(referenced_images)} referenced PNGs and their SVG companions")
    print("See docs/PUBLISHING.md for the handoff into your blog checkout.")


if __name__ == "__main__":
    main()
