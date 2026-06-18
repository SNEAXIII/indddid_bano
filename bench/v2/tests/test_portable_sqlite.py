# tests/test_portable_sqlite.py
from search_bench.data import Record
from search_bench.portable_sqlite import read_portable, write_portable


def test_portable_roundtrip(tmp_path):
    records = [
        Record("Rue de la Paix", "75002", "Paris"),
        Record("Place Bellecour", "69002", "Lyon"),
    ]
    postings = {
        "paix": [0],
        "rue": [0],
        "place": [1],
        "bellecour": [1],
    }
    db_path = str(tmp_path / "portable.db")
    write_portable(db_path, records, postings)

    loaded_records, loaded_postings = read_portable(db_path)
    assert loaded_records == records
    assert loaded_postings["paix"] == [0]
    assert loaded_postings["bellecour"] == [1]
    assert set(loaded_postings.keys()) == set(postings.keys())
