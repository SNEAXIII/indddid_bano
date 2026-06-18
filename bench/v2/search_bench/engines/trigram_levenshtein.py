# search_bench/engines/trigram_levenshtein.py
import time
from collections import defaultdict

from search_bench.data import Record
from search_bench.engines.base import Result, SearchEngine
from search_bench.normalize import tokenize
from search_bench.scoring import score_tokens


def _trigrams(token: str) -> set[str]:
    padded = f"  {token} "
    return {padded[i : i + 3] for i in range(len(padded) - 2)}


class TrigramLevenshtein(SearchEngine):
    name = "trigram_levenshtein"
    supports_fuzzy = True
    #: nb min de trigrammes partagés pour retenir un token candidat
    MIN_SHARED_TRIGRAMS = 1

    def build(self, records: list[Record]) -> None:
        start = time.perf_counter()
        self._records = records
        self._tokens = [r.tokens for r in records]
        self._trigram_to_ids: dict[str, set[int]] = defaultdict(set)
        for rid, toks in enumerate(self._tokens):
            for tok in toks:
                for tg in _trigrams(tok):
                    self._trigram_to_ids[tg].add(rid)
        self.build_time_ms = (time.perf_counter() - start) * 1000
        self.artifact_size_bytes = -1

    def _candidate_ids(self, q: list[str]) -> set[int]:
        counts: dict[int, int] = defaultdict(int)
        for qt in q:
            seen_for_token: set[int] = set()
            for tg in _trigrams(qt):
                for rid in self._trigram_to_ids.get(tg, set()):
                    if rid not in seen_for_token:
                        seen_for_token.add(rid)
                        counts[rid] += 1
        return {rid for rid, c in counts.items() if c >= self.MIN_SHARED_TRIGRAMS}

    def search(self, query: str, limit: int = 10) -> list[Result]:
        q = tokenize(query)
        if not q:
            return []
        scored: list[Result] = []
        for rid in self._candidate_ids(q):
            s = score_tokens(q, self._tokens[rid])
            if s is not None:
                rec = self._records[rid]
                scored.append(Result(rec.voie, rec.code_postal, rec.ville, s))
        scored.sort(key=lambda r: (-r.score, r.voie, r.code_postal, r.ville))
        return scored[:limit]
