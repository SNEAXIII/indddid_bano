# search_bench/metrics.py
"""Métriques de performance et de qualité."""


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[-1]
    rank = (p / 100) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * frac


def _matches(result: dict, target: dict) -> bool:
    return (
        result["voie"] == target["voie"]
        and result["code_postal"] == target["code_postal"]
        and result["ville"] == target["ville"]
    )


def recall_at_k(results: list[dict], target: dict, k: int) -> float:
    return 1.0 if any(_matches(r, target) for r in results[:k]) else 0.0


def reciprocal_rank(results: list[dict], target: dict) -> float:
    for idx, r in enumerate(results, start=1):
        if _matches(r, target):
            return 1.0 / idx
    return 0.0
