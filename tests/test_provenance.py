import json

import pytest

from svd_portfolio.data import sha256
from svd_portfolio.research import source_fingerprint
from svd_portfolio.validation import verify_manifest


def test_presentation_rejects_revised_raw_snapshot(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "uv.lock").write_text("test lock")
    output = tmp_path / "outputs" / "test"
    output.mkdir(parents=True)
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    source = raw / "SPY_2020-01-01_2020-02-01.csv"
    source.write_text("Date,SPY\n2020-01-02,100\n")
    snapshot = {
        "ticker": "SPY",
        "start_inclusive": "2020-01-01",
        "end_exclusive": "2020-02-01",
        "sha256": sha256(source),
    }
    source.with_suffix(".json").write_text(json.dumps(snapshot))
    manifest = {
        "source_sha256": source_fingerprint(tmp_path),
        "uv_lock_sha256": sha256(tmp_path / "uv.lock"),
        "tables_sha256": {},
        "data_audit": {"snapshots": [snapshot]},
    }
    (output / "manifest.json").write_text(json.dumps(manifest))
    verify_manifest(tmp_path, "test")
    source.write_text("Date,SPY\n2020-01-02,101\n")
    with pytest.raises(ValueError, match="Input vintage changed"):
        verify_manifest(tmp_path, "test")
