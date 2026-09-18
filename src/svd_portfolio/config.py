"""Fixed research protocol. Change these before examining a new evaluation sample."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Universe:
    key: str
    title: str
    tickers: tuple[str, ...]
    benchmark: str


UNIVERSES = {
    "us_equity": Universe(
        "us_equity",
        "US sector ETFs",
        ("XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY"),
        "SPY",
    ),
    "multi_asset": Universe(
        "multi_asset",
        "Multi-asset ETFs",
        ("AGG", "DIA", "GLD", "IAGG", "IDEV", "IEMG", "LQD", "QQQ", "SHY", "SPY", "TLT", "VNQ"),
        "AOM",
    ),
}


@dataclass(frozen=True)
class ResearchConfig:
    data_start: str = "2018-07-01"
    data_end: str = "2026-09-01"  # Exclusive; last complete month at protocol creation.
    evaluation_start: str = "2020-08-01"
    test_start: str = "2025-01-01"
    lookback: int = 504
    n_components: int = 3
    weight_cap: float = 0.30
    cost_bps: float = 5.0  # Per dollar bought OR sold.
    pca_space: str = "covariance"
    bootstrap_samples: int = 2000
    block_length: int = 21
    seed: int = 20260917

    def __post_init__(self):
        if self.lookback < 3 or self.n_components < 1:
            raise ValueError("lookback >= 3 and n_components >= 1 are required")
        if not 0 < self.weight_cap <= 1 or not 0 <= self.cost_bps < 10000:
            raise ValueError("Invalid weight cap or trading cost")
        if self.pca_space not in ("covariance", "correlation"):
            raise ValueError("pca_space must be covariance or correlation")
        if self.block_length < 1 or self.bootstrap_samples < 1:
            raise ValueError("Positive bootstrap settings are required")

    def to_dict(self):
        return asdict(self)


STRATEGIES = ("Equal weight", "Inverse volatility", "Sample GMV", "Ledoit-Wolf GMV", "PCA GMV")
ESTIMATORS = ("Sample", "Ledoit-Wolf", "PCA")
