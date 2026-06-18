# tests/test_engines.py
import pytest

from search_bench.engines import ENGINES


def _build(engine_cls, records):
    engine = engine_cls()
    engine.build(records)
    return engine


@pytest.mark.parametrize("engine_cls", ENGINES, ids=lambda c: c.name)
def test_exact_query_returns_target_first(engine_cls, records):
    engine = _build(engine_cls, records)
    results = engine.search("rue de la paix paris", limit=5)
    assert results, f"{engine_cls.name} returned nothing"
    assert results[0].voie == "Rue de la Paix"


@pytest.mark.parametrize("engine_cls", ENGINES, ids=lambda c: c.name)
def test_out_of_order_query(engine_cls, records):
    engine = _build(engine_cls, records)
    results = engine.search("paris paix", limit=5)
    top_voies = [r.voie for r in results]
    if engine_cls.supports_fuzzy or engine_cls.name in {
        "fts5_unicode61",
        "fts5_trigram",
        "like",
    }:
        assert "Rue de la Paix" in top_voies


@pytest.mark.parametrize(
    "engine_cls",
    [c for c in ENGINES if c.supports_fuzzy],
    ids=lambda c: c.name,
)
def test_typo_query_for_fuzzy_engines(engine_cls, records):
    engine = _build(engine_cls, records)
    results = engine.search("rue de la pais paris", limit=5)  # "pais" -> "paix"
    top_voies = [r.voie for r in results]
    assert "Rue de la Paix" in top_voies


@pytest.mark.parametrize("engine_cls", ENGINES, ids=lambda c: c.name)
def test_empty_query_returns_empty(engine_cls, records):
    engine = _build(engine_cls, records)
    assert engine.search("", limit=5) == []


def test_fts5_engines_handle_quote_in_query(records):
    # un token avec un guillemet ne doit PAS planter les moteurs FTS5
    from search_bench.engines.fts5_unicode61 import Fts5Unicode61
    from search_bench.engines.fts5_trigram import Fts5Trigram

    for cls in (Fts5Unicode61, Fts5Trigram):
        engine = cls()
        engine.build(records)
        # ne doit pas lever; le résultat peut être vide
        engine.search('paix"', limit=5)
        engine.close()


def test_close_is_safe_for_all_engines(records):
    for engine_cls in ENGINES:
        engine = engine_cls()
        engine.build(records)
        engine.close()
        engine.close()  # idempotent


def test_tie_break_is_deterministic(records):
    # deux constructions du même moteur donnent le même ordre
    for engine_cls in ENGINES:
        a = engine_cls()
        a.build(records)
        b = engine_cls()
        b.build(records)
        ra = [(r.voie, r.code_postal, r.ville) for r in a.search("rue paris", limit=10)]
        rb = [(r.voie, r.code_postal, r.ville) for r in b.search("rue paris", limit=10)]
        assert ra == rb, f"{engine_cls.name} non déterministe"
        a.close()
        b.close()
