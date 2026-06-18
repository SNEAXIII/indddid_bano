# search_bench/engines/trie_prefix.py
import time

from search_bench.data import Record
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize


class _Node:
    __slots__ = ("children", "record_ids")

    def __init__(self):
        self.children: dict[str, _Node] = {}
        self.record_ids: set[int] = set()


class TriePrefix(SearchEngine):
    name = "trie_prefix"
    supports_fuzzy = False  # préfixe pur, pas de tolérance aux fautes

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._root = _Node()
        for rid, rec in enumerate(records):
            for tok in rec.tokens:
                node = self._root
                for ch in tok:
                    node = node.children.setdefault(ch, _Node())
                    node.record_ids.add(rid)
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = -1

    def _ids_with_prefix(self, prefix: str) -> set[int]:
        node = self._root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return set()
        return node.record_ids

    def search(self, query: str, limit: int = 10) -> list[Result]:
        q = tokenize(query)
        if not q:
            return []
        candidates: set[int] | None = None
        for qt in q:
            ids = self._ids_with_prefix(qt)
            candidates = ids if candidates is None else (candidates & ids)
            if not candidates:
                return []
        results = [
            Result(
                self._records[i].voie,
                self._records[i].code_postal,
                self._records[i].ville,
                1.0,
            )
            for i in candidates
        ]
        results.sort(key=lambda r: r.voie)
        return results[:limit]
