# tests/test_data.py
import csv
from search_bench.data import Record, load_records


def test_load_records(tmp_path):
    p = tmp_path / "streets.csv"
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["voie", "code_postal", "ville"])
        w.writerow(["Rue de la Paix", "75002", "Paris"])
        w.writerow(["", "13001", "Marseille"])  # malformed: empty voie -> skipped
    records = load_records(str(p))
    assert len(records) == 1
    assert records[0] == Record(
        voie="Rue de la Paix", code_postal="75002", ville="Paris"
    )
    assert records[0].search_text == "rue de la paix 75002 paris"


def test_record_caches_derived_values_and_equality_ignores_them():
    r1 = Record("Rue de la Paix", "75002", "Paris")
    r2 = Record("Rue de la Paix", "75002", "Paris")
    assert r1 == r2  # equality only on the 3 fields
    assert r1.tokens == ["rue", "de", "la", "paix", "75002", "paris"]
    # cached: same object returned on repeated access
    assert r1.tokens is r1.tokens
