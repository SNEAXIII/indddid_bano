"""Distance d'édition + scoring fuzzy tolérant à l'ordre des mots."""

from typing import Optional


def levenshtein(a: str, b: str) -> int:
    """Distance d'édition classique (insertion/suppression/substitution)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
            )
        previous = current
    return previous[-1]


def similarity(query_tok: str, record_tok: str) -> float:
    """1.0 = identique. Bonus si query_tok est un préfixe de record_tok (saisie en cours)."""
    if query_tok == record_tok:
        return 1.0
    if record_tok.startswith(query_tok):
        return 0.9 + 0.1 * (len(query_tok) / len(record_tok))
    longest = max(len(query_tok), len(record_tok))
    if longest == 0:
        return 1.0
    return 1.0 - levenshtein(query_tok, record_tok) / longest


def score_tokens(
    query_tokens: list[str],
    record_tokens: list[str],
    threshold: float = 0.7,
) -> Optional[float]:
    """Pour chaque token requête, prend la meilleure similarité parmi les tokens du record.

    Tolère l'ordre des mots (chaque token requête est apparié indépendamment).
    Retourne None si un token requête n'atteint le seuil sur aucun token du record.
    Sinon retourne la similarité moyenne (0..1).
    """
    if not query_tokens or not record_tokens:
        return None
    query_tokens = [qt for qt in query_tokens if qt]
    if not query_tokens:
        return None
    total = 0.0
    for qt in query_tokens:
        best = max(similarity(qt, rt) for rt in record_tokens)
        if best < threshold:
            return None
        total += best
    return total / len(query_tokens)
