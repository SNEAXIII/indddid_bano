# search_bench/export_android.py
"""Exporte les moteurs survivants en SQLite portable pour Android."""

import os
import shutil

from search_bench.data import Record
from search_bench.engines import ENGINES
from search_bench.portable_sqlite import write_portable

_ENGINE_BY_NAME = {e.name: e for e in ENGINES}
_SQL_ENGINES = {"like", "fts5_unicode61", "fts5_trigram"}


def _postings_of(records: list[Record]) -> dict[str, list[int]]:
    postings: dict[str, list[int]] = {}
    for rid, rec in enumerate(records):
        for tok in set(rec.tokens):
            postings.setdefault(tok, []).append(rid)
    return postings


def export_survivors(
    artifacts_dir: str, survivors: list[str], out_dir: str
) -> dict[str, str]:
    """Pour chaque survivant connu, écrit out_dir/<name>.db. Retourne {name: path}."""
    os.makedirs(out_dir, exist_ok=True)
    written: dict[str, str] = {}
    for name in survivors:
        engine_cls = _ENGINE_BY_NAME.get(name)
        if engine_cls is None:
            continue  # survivant inconnu -> ignoré
        engine_dir = os.path.join(artifacts_dir, name)
        out_path = os.path.join(out_dir, f"{name}.db")
        try:
            if name in _SQL_ENGINES:
                shutil.copyfile(os.path.join(engine_dir, "index.db"), out_path)
            else:
                engine = engine_cls.load(engine_dir)
                try:
                    records = engine._records
                    postings = _postings_of(records)
                    write_portable(out_path, records, postings)
                finally:
                    engine.close()
            written[name] = out_path
        except Exception as exc:  # artefact manquant/corrompu -> on saute, on continue
            import sys

            print(f"  ! {name}: export ignoré ({exc})", file=sys.stderr)
    return written


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Export Android SQLite des survivantes"
    )
    parser.add_argument("-a", "--artifacts", default="shared/artifacts")
    parser.add_argument("-o", "--out-dir", default="shared/android")
    parser.add_argument(
        "-r",
        "--report",
        default="reports/report.json",
        help="report.json dont on lit la liste 'survivors' (sauf si --survivors fourni)",
    )
    parser.add_argument(
        "-s",
        "--survivors",
        nargs="*",
        default=None,
        help="liste explicite de survivantes (sinon lue depuis --report)",
    )
    args = parser.parse_args()

    survivors = args.survivors
    if survivors is None:
        with open(args.report, encoding="utf-8") as f:
            data = json.load(f)
        survivors = data.get("survivors")
        if survivors is None:
            raise SystemExit(f"'{args.report}' ne contient pas de clé 'survivors'")
    written = export_survivors(args.artifacts, survivors, args.out_dir)
    for name, path in written.items():
        size_mo = os.path.getsize(path) / 1e6
        print(f"  ✓ {name:22s} -> {path}  ({size_mo:.1f} Mo)")
    if not written:
        print("⚠ aucune survivante exportée (liste vide ou artefacts manquants)")
    print(f"✓ {len(written)} artefact(s) Android écrit(s) dans {args.out_dir}/")


if __name__ == "__main__":
    main()
