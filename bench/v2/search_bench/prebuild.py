# search_bench/prebuild.py
"""Construit chaque moteur UNE fois, persiste l'artefact, écrit un manifeste."""

import json
import os

from search_bench.data import Record, load_records
from search_bench.engines import ENGINES


def prebuild_all(records: list[Record], artifacts_dir: str) -> dict:
    os.makedirs(artifacts_dir, exist_ok=True)
    manifest: dict = {}
    for engine_cls in ENGINES:
        engine = engine_cls()
        try:
            engine.build(records)
            engine_dir = os.path.join(artifacts_dir, engine_cls.name)
            engine.save(engine_dir)
            manifest[engine_cls.name] = {
                "build_time_ms": round(engine.build_time_ms, 2),
                "artifact_size_bytes": engine.artifact_size_bytes,
            }
        finally:
            engine.close()
    with open(os.path.join(artifacts_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Prebuild des artefacts de tous les moteurs"
    )
    parser.add_argument("-i", "--input", default="../../data/streets.csv")
    parser.add_argument("-o", "--out-dir", default="shared/artifacts")
    parser.add_argument(
        "-m",
        "--max-records",
        type=int,
        default=None,
        help="limite le nombre de lignes chargées (défaut : tout)",
    )
    args = parser.parse_args()

    records = load_records(args.input, limit=args.max_records)
    print(f"→ {len(records):,} adresses chargées")
    manifest = prebuild_all(records, args.out_dir)
    for name, m in manifest.items():
        size_mo = m["artifact_size_bytes"] / 1e6
        print(
            f"  ✓ {name:22s} build={m['build_time_ms']:>9.1f} ms  taille={size_mo:7.1f} Mo"
        )
    print(f"✓ Artefacts + manifeste écrits dans {args.out_dir}/")


if __name__ == "__main__":
    main()
