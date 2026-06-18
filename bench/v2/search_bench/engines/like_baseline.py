# search_bench/engines/like_baseline.py
import os
import time

from search_bench.data import Record
from search_bench.engines._artifact import dir_size_bytes, read_meta, write_meta
from search_bench.engines._sqlite_base import (
    file_size,
    finalize_db,
    open_db_at,
    open_existing_db,
    open_temp_db,
)
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize


def _create_schema(conn) -> None:
    conn.execute(
        "CREATE TABLE adresses("
        "rid INTEGER PRIMARY KEY, voie TEXT, code_postal TEXT, ville TEXT, text TEXT)"
    )


def _fill(conn, records: list[Record]) -> None:
    conn.executemany(
        "INSERT INTO adresses(rid, voie, code_postal, ville, text) VALUES (?, ?, ?, ?, ?)",
        [
            (i, r.voie, r.code_postal, r.ville, r.search_text)
            for i, r in enumerate(records)
        ],
    )
    conn.commit()


def _load_records(conn) -> list[Record]:
    rows = conn.execute(
        "SELECT voie, code_postal, ville FROM adresses ORDER BY rid"
    ).fetchall()
    return [Record(v, c, w) for v, c, w in rows]


class LikeBaseline(SearchEngine):
    name = "like"
    supports_fuzzy = False

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._conn, path = open_temp_db(self.name)
        _create_schema(self._conn)
        _fill(self._conn, records)
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = file_size(path)

    def save(self, artifact_dir: str) -> None:
        db_path = os.path.join(artifact_dir, "index.db")
        conn = open_db_at(db_path)
        _create_schema(conn)
        _fill(conn, self._records)
        finalize_db(conn)
        conn.close()
        self.artifact_size_bytes = dir_size_bytes(artifact_dir)
        write_meta(artifact_dir, self.build_time_ms, self.artifact_size_bytes)

    @classmethod
    def load(cls, artifact_dir: str) -> "LikeBaseline":
        engine = cls()
        engine._conn = open_existing_db(os.path.join(artifact_dir, "index.db"))
        engine._records = _load_records(engine._conn)
        meta = read_meta(artifact_dir)
        engine.build_time_ms = meta["build_time_ms"]
        engine.artifact_size_bytes = meta["artifact_size_bytes"]
        return engine

    def search(self, query: str, limit: int = 10) -> list[Result]:
        q = tokenize(query)
        if not q:
            return []
        where = " AND ".join("text LIKE ?" for _ in q)
        params = [f"%{tok}%" for tok in q]
        rows = self._conn.execute(
            f"SELECT voie, code_postal, ville FROM adresses WHERE {where} LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [Result(v, c, w, 1.0) for v, c, w in rows]

    def close(self) -> None:
        conn = getattr(self, "_conn", None)
        if conn is not None:
            conn.close()
