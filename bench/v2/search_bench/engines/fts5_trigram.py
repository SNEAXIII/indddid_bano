# search_bench/engines/fts5_trigram.py
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
        'CREATE VIRTUAL TABLE adresses USING fts5(text, content="", tokenize="trigram")'
    )
    conn.execute(
        "CREATE TABLE records(rid INTEGER PRIMARY KEY, voie TEXT, code_postal TEXT, ville TEXT)"
    )


def _fill(conn, records: list[Record]) -> None:
    conn.executemany(
        "INSERT INTO adresses(rowid, text) VALUES (?, ?)",
        [(i, r.search_text) for i, r in enumerate(records)],
    )
    conn.executemany(
        "INSERT INTO records(rid, voie, code_postal, ville) VALUES (?, ?, ?, ?)",
        [(i, r.voie, r.code_postal, r.ville) for i, r in enumerate(records)],
    )
    conn.commit()


def _load_records(conn) -> list[Record]:
    rows = conn.execute(
        "SELECT voie, code_postal, ville FROM records ORDER BY rid"
    ).fetchall()
    return [Record(v, c, w) for v, c, w in rows]


class Fts5Trigram(SearchEngine):
    name = "fts5_trigram"
    supports_fuzzy = (
        False  # trigram ne tolère que les fautes préservant un trigramme complet
    )

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._conn, path = open_temp_db(self.name)
        _create_schema(self._conn)
        _fill(self._conn, records)
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = file_size(path)

    def save(self, artifact_dir: str) -> None:
        conn = open_db_at(os.path.join(artifact_dir, "index.db"))
        _create_schema(conn)
        _fill(conn, self._records)
        finalize_db(conn)
        conn.close()
        self.artifact_size_bytes = dir_size_bytes(artifact_dir)
        write_meta(artifact_dir, self.build_time_ms, self.artifact_size_bytes)

    @classmethod
    def load(cls, artifact_dir: str) -> "Fts5Trigram":
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
        terms = [tok for tok in q if len(tok) >= 3]
        if not terms:
            return []
        match = " AND ".join('"' + tok.replace('"', '""') + '"' for tok in terms)
        rows = self._conn.execute(
            "SELECT rowid, rank FROM adresses WHERE adresses MATCH ? ORDER BY rank LIMIT ?",
            (match, limit),
        ).fetchall()
        out: list[Result] = []
        for rid, rank in rows:
            rec = self._records[rid]
            out.append(Result(rec.voie, rec.code_postal, rec.ville, -float(rank)))
        return out

    def close(self) -> None:
        conn = getattr(self, "_conn", None)
        if conn is not None:
            conn.close()
