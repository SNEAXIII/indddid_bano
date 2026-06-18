# tests/test_export_android.py
import os

from search_bench.export_android import export_survivors
from search_bench.portable_sqlite import read_portable
from search_bench.prebuild import prebuild_all


def test_export_survivors_writes_portable_db(records, tmp_path):
    artifacts = str(tmp_path / "artifacts")
    prebuild_all(records, artifacts)
    out = str(tmp_path / "android")

    survivors = ["fts5_trigram", "inverted_index"]
    written = export_survivors(artifacts, survivors, out)

    for name in survivors:
        path = os.path.join(out, f"{name}.db")
        assert os.path.exists(path), f"{name} not exported"
        assert written[name] == path

    recs, postings = read_portable(os.path.join(out, "inverted_index.db"))
    assert len(recs) == len(records)
    paix_idx = next(i for i, r in enumerate(records) if r.voie == "Rue de la Paix")
    assert paix_idx in postings["paix"]


def test_export_skips_unknown_survivor(records, tmp_path):
    artifacts = str(tmp_path / "artifacts")
    prebuild_all(records, artifacts)
    out = str(tmp_path / "android")
    written = export_survivors(artifacts, ["does_not_exist"], out)
    assert written == {}


def test_export_skips_survivor_with_missing_artifact(records, tmp_path):
    artifacts = str(tmp_path / "artifacts")
    prebuild_all(records, artifacts)
    out = str(tmp_path / "android")
    # "trie_prefix" is prebuilt, "inverted_index" artifact removed -> must be skipped, not crash
    import shutil

    shutil.rmtree(os.path.join(artifacts, "inverted_index"))
    written = export_survivors(artifacts, ["trie_prefix", "inverted_index"], out)
    assert "trie_prefix" in written
    assert "inverted_index" not in written  # skipped gracefully
    assert os.path.exists(written["trie_prefix"])
