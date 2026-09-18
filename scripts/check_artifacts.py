"""Independently reconcile cached source snapshots, holdings and published statistics."""

import json
from pathlib import Path

from svd_portfolio.config import UNIVERSES
from svd_portfolio.validation import verify_accounting

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = [verify_accounting(ROOT, key) for key in UNIVERSES]
    target = ROOT / "research" / "results"
    target.mkdir(parents=True, exist_ok=True)
    (target / "independent_validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
