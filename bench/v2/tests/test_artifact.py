# tests/test_artifact.py
import json

from search_bench.engines._artifact import (
    dir_size_bytes,
    pack_ids,
    read_meta,
    unpack_ids,
    write_meta,
)


def test_pack_unpack_roundtrip():
    ids = [0, 1, 5, 2_000_000, 42]
    blob = pack_ids(ids)
    assert isinstance(blob, (bytes, bytearray))
    assert unpack_ids(blob) == ids


def test_pack_empty():
    assert unpack_ids(pack_ids([])) == []


def test_meta_roundtrip(tmp_path):
    write_meta(str(tmp_path), build_time_ms=12.5, artifact_size_bytes=999)
    meta = read_meta(str(tmp_path))
    assert meta == {"build_time_ms": 12.5, "artifact_size_bytes": 999}
    on_disk = json.loads((tmp_path / "meta.json").read_text())
    assert on_disk["artifact_size_bytes"] == 999


def test_dir_size_counts_files(tmp_path):
    (tmp_path / "a.bin").write_bytes(b"x" * 10)
    (tmp_path / "b.bin").write_bytes(b"y" * 5)
    assert dir_size_bytes(str(tmp_path)) == 15
