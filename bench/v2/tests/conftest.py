# tests/conftest.py
import pytest

from search_bench.data import Record

FIXTURE_RECORDS = [
    Record("Rue de la Paix", "75002", "Paris"),
    Record("Avenue des Champs-Élysées", "75008", "Paris"),
    Record("Rue de la République", "13001", "Marseille"),
    Record("Boulevard de la Liberté", "59000", "Lille"),
    Record("Place Bellecour", "69002", "Lyon"),
    Record("Rue Sainte-Catherine", "33000", "Bordeaux"),
]


@pytest.fixture
def records():
    return list(FIXTURE_RECORDS)
