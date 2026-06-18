# tests/test_normalize.py
from search_bench.normalize import normalize, tokenize


def test_lowercases_and_strips_accents():
    assert normalize("Rue de l'Égalité") == "rue de l egalite"


def test_hyphen_and_apostrophe_become_space():
    assert normalize("Saint-Étienne-du-Rouvray") == "saint etienne du rouvray"


def test_collapses_and_trims_spaces():
    assert normalize("  rue   des    lilas ") == "rue des lilas"


def test_tokenize_splits_on_space():
    assert tokenize("Rue de la Paix") == ["rue", "de", "la", "paix"]


def test_tokenize_empty():
    assert tokenize("   ") == []
