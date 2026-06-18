# search_bench/engines/parquet_scan.py
import os
import tempfile
import time

import pyarrow as pa
import pyarrow.parquet as pq

from search_bench.data import Record
from search_bench.engines._artifact import dir_size_bytes, read_meta, write_meta
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize
from search_bench.scoring import score_tokens


def _records_to_table(records: list[Record]) -> pa.Table:
    return pa.table(
        {
            "voie": [r.voie for r in records],
            "code_postal": [r.code_postal for r in records],
            "ville": [r.ville for r in records],
        }
    )


def _table_to_records(table: pa.Table) -> list[Record]:
    return [
        Record(v, c, w)
        for v, c, w in zip(
            table.column("voie").to_pylist(),
            table.column("code_postal").to_pylist(),
            table.column("ville").to_pylist(),
        )
    ]


class ParquetScan(SearchEngine):
    name = "parquet_scan"
    supports_fuzzy = True

    def build(self, records: list[Record]) -> None:
        # build_time inclut volontairement write + reload (coût du round-trip colonnaire)
        start = time.perf_counter()
        path = os.path.join(tempfile.gettempdir(), f"bano_bench_{self.name}.parquet")
        pq.write_table(_records_to_table(records), path, compression="snappy")
        loaded = pq.read_table(path)
        self._records = _table_to_records(loaded)
        self._tokens = [r.tokens for r in self._records]
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = os.path.getsize(path)

    def save(self, artifact_dir: str) -> None:
        os.makedirs(artifact_dir, exist_ok=True)
        pq.write_table(
            _records_to_table(self._records),
            os.path.join(artifact_dir, "data.parquet"),
            compression="snappy",
        )
        self.artifact_size_bytes = dir_size_bytes(artifact_dir)
        write_meta(artifact_dir, self.build_time_ms, self.artifact_size_bytes)

    @classmethod
    def load(cls, artifact_dir: str) -> "ParquetScan":
        engine = cls()
        table = pq.read_table(os.path.join(artifact_dir, "data.parquet"))
        engine._records = _table_to_records(table)
        engine._tokens = [r.tokens for r in engine._records]
        meta = read_meta(artifact_dir)
        engine.build_time_ms = meta["build_time_ms"]
        engine.artifact_size_bytes = meta["artifact_size_bytes"]
        return engine

    def search(self, query: str, limit: int = 10) -> list[Result]:
        q = tokenize(query)
        if not q:
            return []
        scored: list[Result] = []
        for rec, toks in zip(self._records, self._tokens):
            s = score_tokens(q, toks)
            if s is not None:
                scored.append(Result(rec.voie, rec.code_postal, rec.ville, s))
        scored.sort(key=lambda r: (-r.score, r.voie, r.code_postal, r.ville))
        return scored[:limit]
