# search_bench/engines/inverted_index.py
import time
from collections import defaultdict

from search_bench.data import Record
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize
from search_bench.scoring import score_tokens


def _trigrams(token: str) -> set[str]:
    padded = f"  {token} "
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


class InvertedIndex(SearchEngine):
    name = "inverted_index"
    supports_fuzzy = True

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._tokens = [r.tokens for r in records]
        self._postings: dict[str, set[int]] = defaultdict(set)
        self._trigram_to_tokens: dict[str, set[str]] = defaultdict(set)
        for rid, toks in enumerate(self._tokens):
            for tok in toks:
                self._postings[tok].add(rid)
                for tg in _trigrams(tok):
                    self._trigram_to_tokens[tg].add(tok)
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = -1

    def _candidate_tokens(self, qt: str) -> set[str]:
        cands: set[str] = set()
        for tg in _trigrams(qt):
            cands |= self._trigram_to_tokens.get(tg, set())
        cands |= {t for t in self._postings if t.startswith(qt)}
        return cands

    def search(self, query: str, limit: int = 10) -> list[Result]:
        q = tokenize(query)
        if not q:
            return []
        candidate_ids: set[int] = set()
        for qt in q:
            for tok in self._candidate_tokens(qt):
                candidate_ids |= self._postings.get(tok, set())
        scored: list[Result] = []
        for rid in candidate_ids:
            s = score_tokens(q, self._tokens[rid])
            if s is not None:
                rec = self._records[rid]
                scored.append(Result(rec.voie, rec.code_postal, rec.ville, s))
        scored.sort(key=lambda r: (-r.score, r.voie, r.code_postal, r.ville))
        return scored[:limit]
