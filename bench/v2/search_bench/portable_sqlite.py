# search_bench/portable_sqlite.py
"""Format d'artefact portable Android : un .db SQLite (records + postings BLOB int32).

Schéma (lisible en Java via android.database.sqlite + ByteBuffer) :
  records(rid INTEGER PRIMARY KEY, voie TEXT, code_postal TEXT, ville TEXT)
  tokens(token TEXT PRIMARY KEY, postings BLOB)   -- int32 little-endian
"""

from search_bench.data import Record
from search_bench.engines._artifact import pack_ids, unpack_ids
from search_bench.engines._sqlite_base import finalize_db, open_db_at, open_existing_db


def write_portable(
    db_path: str, records: list[Record], postings: dict[str, list[int]]
) -> None:
    conn = open_db_at(db_path)
    try:
        conn.execute(
            "CREATE TABLE records(rid INTEGER PRIMARY KEY, voie TEXT, code_postal TEXT, ville TEXT)"
        )
        conn.execute("CREATE TABLE tokens(token TEXT PRIMARY KEY, postings BLOB)")
        conn.executemany(
            "INSERT INTO records(rid, voie, code_postal, ville) VALUES (?, ?, ?, ?)",
            [(i, r.voie, r.code_postal, r.ville) for i, r in enumerate(records)],
        )
        conn.executemany(
            "INSERT INTO tokens(token, postings) VALUES (?, ?)",
            [(tok, pack_ids(sorted(ids))) for tok, ids in postings.items()],
        )
        conn.commit()
        finalize_db(conn)
    finally:
        conn.close()


def read_portable(db_path: str) -> tuple[list[Record], dict[str, list[int]]]:
    conn = open_existing_db(db_path)
    try:
        rec_rows = conn.execute(
            "SELECT voie, code_postal, ville FROM records ORDER BY rid"
        ).fetchall()
        records = [Record(v, c, w) for v, c, w in rec_rows]
        postings: dict[str, list[int]] = {}
        for token, blob in conn.execute("SELECT token, postings FROM tokens"):
            postings[token] = unpack_ids(blob)
    finally:
        conn.close()
    return records, postings
