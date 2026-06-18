# tests/test_prebuild.py
import json
import os

from search_bench.prebuild import prebuild_all


def test_prebuild_writes_artifacts_and_manifest(records, tmp_path):
    out = str(tmp_path / "artifacts")
    manifest = prebuild_all(records, out)
    from search_bench.engines import ENGINES

    names = {e.name for e in ENGINES}
    assert set(manifest.keys()) == names
    for name in names:
        assert os.path.isdir(os.path.join(out, name))
        assert os.path.exists(os.path.join(out, name, "meta.json"))
        assert manifest[name]["artifact_size_bytes"] > 0
        assert manifest[name]["build_time_ms"] >= 0
    on_disk = json.loads((tmp_path / "artifacts" / "manifest.json").read_text())
    assert set(on_disk.keys()) == names
