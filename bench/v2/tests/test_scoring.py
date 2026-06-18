from search_bench.scoring import levenshtein, similarity, score_tokens


def test_levenshtein_basic():
    assert levenshtein("paix", "paix") == 0
    assert levenshtein("paix", "pais") == 1
    assert levenshtein("paix", "") == 4


def test_similarity_identical_is_one():
    assert similarity("paris", "paris") == 1.0


def test_similarity_typo_is_high():
    assert similarity("paris", "pariss") > 0.7


def test_score_tokens_out_of_order_matches():
    score = score_tokens(
        ["paix", "paris"], ["rue", "de", "la", "paix", "paris"], threshold=0.7
    )
    assert score is not None and score > 0.8


def test_score_tokens_below_threshold_returns_none():
    score = score_tokens(["xyzzy"], ["rue", "de", "la", "paix"], threshold=0.7)
    assert score is None


def test_score_tokens_prefix_bonus():
    score = score_tokens(["pa"], ["paix"], threshold=0.7)
    assert score is not None


def test_score_tokens_ignores_empty_query_tokens():
    # empty tokens must not cause spurious matches
    assert score_tokens(["", ""], ["rue", "paix"], threshold=0.7) is None
    # a real token alongside empties still scores on its own merit
    s = score_tokens(["paix", ""], ["rue", "de", "la", "paix"], threshold=0.7)
    assert s is not None and s > 0.9
