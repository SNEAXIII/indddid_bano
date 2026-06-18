# tests/test_save_load.py
import pytest

from search_bench.engines.csv_scan import CsvLinearScan
from search_bench.engines.trie_prefix import TriePrefix
from search_bench.engines.inverted_index import InvertedIndex
from search_bench.engines.trigram_levenshtein import TrigramLevenshtein

PICKLE_ENGINES = [CsvLinearScan, TriePrefix, InvertedIndex, TrigramLevenshtein]


@pytest.mark.parametrize("engine_cls", PICKLE_ENGINES, ids=lambda c: c.name)
def test_save_load_roundtrip(engine_cls, records, tmp_path):
    built = engine_cls()
    built.build(records)
    artifact_dir = str(tmp_path / engine_cls.name)
    built.save(artifact_dir)

    loaded = engine_cls.load(artifact_dir)
    q = "rue de la paix paris"
    before = [(r.voie, round(r.score, 6)) for r in built.search(q, limit=5)]
    after = [(r.voie, round(r.score, 6)) for r in loaded.search(q, limit=5)]
    assert before == after
    assert loaded.artifact_size_bytes >= 0
    assert loaded.build_time_ms == built.build_time_ms
    built.close()
    loaded.close()


from search_bench.engines.like_baseline import LikeBaseline
from search_bench.engines.fts5_unicode61 import Fts5Unicode61
from search_bench.engines.fts5_trigram import Fts5Trigram


@pytest.mark.parametrize(
    "engine_cls", [LikeBaseline, Fts5Unicode61, Fts5Trigram], ids=lambda c: c.name
)
def test_sql_save_load_roundtrip(engine_cls, records, tmp_path):
    import os

    built = engine_cls()
    built.build(records)
    artifact_dir = str(tmp_path / engine_cls.name)
    built.save(artifact_dir)
    assert os.path.exists(os.path.join(artifact_dir, "index.db")), (
        "save() must write index.db"
    )
    built.close()

    loaded = engine_cls.load(artifact_dir)
    results = loaded.search("rue de la paix paris", limit=5)
    assert any(r.voie == "Rue de la Paix" for r in results)
    loaded.close()


def test_fts5_contentless_still_searches_after_save(records, tmp_path):
    from search_bench.engines.fts5_unicode61 import Fts5Unicode61

    e = Fts5Unicode61()
    e.build(records)
    d = str(tmp_path / "fts5u")
    e.save(d)
    e.close()
    loaded = Fts5Unicode61.load(d)
    res = loaded.search("rue de la paix paris", limit=5)
    assert any(r.voie == "Rue de la Paix" for r in res)
    loaded.close()


def test_like_single_table_after_save(records, tmp_path):
    from search_bench.engines.like_baseline import LikeBaseline

    e = LikeBaseline()
    e.build(records)
    d = str(tmp_path / "like")
    e.save(d)
    e.close()
    loaded = LikeBaseline.load(d)
    res = loaded.search("rue de la paix paris", limit=5)
    assert any(r.voie == "Rue de la Paix" for r in res)
    loaded.close()


from search_bench.engines.parquet_scan import ParquetScan
from search_bench.engines.arrow_scan import ArrowScan


@pytest.mark.parametrize("engine_cls", [ParquetScan, ArrowScan], ids=lambda c: c.name)
def test_columnar_save_load_roundtrip(engine_cls, records, tmp_path):
    import os

    built = engine_cls()
    built.build(records)
    artifact_dir = str(tmp_path / engine_cls.name)
    built.save(artifact_dir)
    expected = "data.parquet" if engine_cls.name == "parquet_scan" else "data.arrow"
    assert os.path.exists(os.path.join(artifact_dir, expected)), (
        "save() must write the native columnar file"
    )
    loaded = engine_cls.load(artifact_dir)
    q = "rue de la paix paris"
    before = [(r.voie, round(r.score, 6)) for r in built.search(q, limit=5)]
    after = [(r.voie, round(r.score, 6)) for r in loaded.search(q, limit=5)]
    assert before == after
    assert loaded.artifact_size_bytes > 0
    built.close()
    loaded.close()
