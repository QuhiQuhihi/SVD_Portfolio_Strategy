"""Offline public-file checks; does not imply full data or publication rights review."""

import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def main():
    for name in (
        "research/AUDIT.md",
        "research/PROTOCOL.md",
        "research/SOURCES.md",
        "research/data/input_manifest.json",
        "research/WORKLOG.md",
        "PUBLICATION.md",
    ):
        if not (ROOT / name).is_file():
            raise ValueError(f"Missing deliverable: {name}")
    for path in [
        ROOT / "README.md",
        ROOT / "PUBLICATION.md",
        *(ROOT / "docs").glob("*.md"),
        *(ROOT / "research").glob("*.md"),
    ]:
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if re.match(r"https?://|mailto:|#", link):
                continue
            target = link.split("#")[0]
            if target and not (path.parent / target).exists():
                raise ValueError(f"Broken link in {path.name}: {target}")
    for name in ("SVD-US_Equity.ipynb", "SVD-Multi_Asset.ipynb"):
        nb = nbformat.read(ROOT / name, as_version=4)
        nbformat.validate(nb)
        code = [c for c in nb.cells if c.cell_type == "code"]
        if any(c.execution_count is None for c in code):
            raise ValueError(f"Unexecuted notebook: {name}")
        if any(o.output_type == "error" for c in code for o in c.outputs):
            raise ValueError(f"Notebook error: {name}")
        print(f"{name}: {len(code)} executed code cells")
    print("Public links, figures and source/evidence registers checked")


if __name__ == "__main__":
    main()
