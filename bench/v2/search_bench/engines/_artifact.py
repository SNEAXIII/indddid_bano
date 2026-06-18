# search_bench/engines/_artifact.py
"""Helpers partagés pour la persistance des artefacts."""

import array
import json
import os


def pack_ids(ids: list[int]) -> bytes:
    """Sérialise une liste d'entiers en BLOB int32 little-endian (lisible en Java via ByteBuffer)."""
    arr = array.array("i", ids)  # 'i' = signed int32
    if arr.itemsize != 4:
        raise RuntimeError("int size attendu = 4 octets")
    import sys

    if sys.byteorder == "big":
        arr.byteswap()
    return arr.tobytes()


def unpack_ids(blob: bytes) -> list[int]:
    """Inverse de pack_ids."""
    arr = array.array("i")
    arr.frombytes(blob)
    import sys

    if sys.byteorder == "big":
        arr.byteswap()
    return list(arr)


def write_meta(
    artifact_dir: str, build_time_ms: float, artifact_size_bytes: int
) -> None:
    os.makedirs(artifact_dir, exist_ok=True)
    with open(os.path.join(artifact_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "build_time_ms": build_time_ms,
                "artifact_size_bytes": artifact_size_bytes,
            },
            f,
        )


def read_meta(artifact_dir: str) -> dict:
    with open(os.path.join(artifact_dir, "meta.json"), encoding="utf-8") as f:
        return json.load(f)


def dir_size_bytes(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(root, name))
    return total
