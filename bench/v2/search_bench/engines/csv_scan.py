# search_bench/engines/csv_scan.py
import time

from search_bench.data import Record
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize
from search_bench.scoring import score_tokens


class CsvLinearScan(SearchEngine):
    name = "csv_scan"
    supports_fuzzy = True

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._tokens = [r.tokens for r in records]
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = -1  # purement en mémoire

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
