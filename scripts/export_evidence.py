"""Export compact verified evidence without redistributing raw price histories."""

import json
import shutil
from pathlib import Path

from svd_portfolio.config import UNIVERSES
from svd_portfolio.validation import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def main():
    for key in UNIVERSES:
        manifest = verify_manifest(ROOT, key)
        target = ROOT / "research" / "results" / key
        target.mkdir(parents=True, exist_ok=True)
        for name in (
            "metrics",
            "annual_metrics",
            "volatility_intervals",
            "forecast_metrics",
            "forecast_intervals",
            "sensitivity",
        ):
            shutil.copyfile(ROOT / "outputs" / key / f"{name}.csv", target / f"{name}.csv")
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Exported verified aggregate evidence for both universes")


if __name__ == "__main__":
    main()
