# tests/test_queryset.py
from search_bench.queryset.generate import generate_queries


def test_generator_is_deterministic(records):
    a = generate_queries(records, n_targets=4, seed=42)
    b = generate_queries(records, n_targets=4, seed=42)
    assert a == b


def test_each_query_has_target_and_kind(records):
    queries = generate_queries(records, n_targets=4, seed=1)
    assert queries, "no queries generated"
    for item in queries:
        assert set(item.keys()) == {"query", "kind", "target"}
        assert item["kind"] in {"prefix", "typo", "shuffle"}
        t = item["target"]
        assert set(t.keys()) == {"voie", "code_postal", "ville"}


def test_query_strings_are_non_empty(records):
    for item in generate_queries(records, n_targets=4, seed=7):
        assert item["query"].strip()
