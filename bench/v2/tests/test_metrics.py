from search_bench.metrics import percentile, recall_at_k, reciprocal_rank


def test_percentile():
    data = [10, 20, 30, 40, 50]
    assert percentile(data, 50) == 30
    assert percentile(data, 100) == 50
    assert percentile(data, 0) == 10


def test_recall_at_k_hit():
    target = {"voie": "Rue de la Paix", "code_postal": "75002", "ville": "Paris"}
    results = [{"voie": "Rue de la Paix", "code_postal": "75002", "ville": "Paris"}]
    assert recall_at_k(results, target, k=5) == 1.0


def test_recall_at_k_miss():
    target = {"voie": "X", "code_postal": "0", "ville": "Y"}
    results = [{"voie": "Rue de la Paix", "code_postal": "75002", "ville": "Paris"}]
    assert recall_at_k(results, target, k=5) == 0.0


def test_reciprocal_rank():
    target = {"voie": "B", "code_postal": "2", "ville": "Z"}
    results = [
        {"voie": "A", "code_postal": "1", "ville": "Z"},
        {"voie": "B", "code_postal": "2", "ville": "Z"},
    ]
    assert reciprocal_rank(results, target) == 0.5
