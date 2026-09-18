"""Download/cache source prices and run both reproducible experiments."""

import argparse
import os
from pathlib import Path

from svd_portfolio.config import UNIVERSES, ResearchConfig
from svd_portfolio.research import run_study


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--universe", choices=["all", *UNIVERSES], default="all")
    parser.add_argument("--download", action="store_true", help="Fetch missing price snapshots")
    parser.add_argument("--refresh", action="store_true", help="Replace existing snapshots")
    parser.add_argument("--sensitivity", action="store_true", help="Run all declared ablations")
    args = parser.parse_args()
    if args.refresh and not args.download:
        parser.error("--refresh requires --download")
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache" / "matplotlib"))
    keys = list(UNIVERSES) if args.universe == "all" else [args.universe]
    for key in keys:
        print(f"Running {key} ...", flush=True)
        study = run_study(
            UNIVERSES[key],
            ResearchConfig(),
            root,
            download=args.download,
            refresh=args.refresh,
            sensitivity=args.sensitivity,
        )
        subset = study["metrics"].query("period == 'historical_test'")
        print(
            subset[["strategy", "cagr", "annualized_volatility", "max_drawdown"]].to_string(
                index=False, float_format=lambda x: f"{x:.4f}"
            ),
            flush=True,
        )
        print(f"Saved {root / 'outputs' / key}", flush=True)


if __name__ == "__main__":
    main()
