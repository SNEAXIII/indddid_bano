# search_bench/normalize.py
"""Règle de normalisation partagée (doit rester identique côté Java)."""

import unicodedata


def normalize(text: str) -> str:
    """minuscules -> sans diacritiques -> ' et - en espace -> espaces compactés."""
    text = text.lower()
    text = text.replace("'", " ").replace("-", " ")
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(stripped.split())


def tokenize(text: str) -> list[str]:
    """Normalise puis découpe en tokens non vides."""
    normalized = normalize(text)
    return normalized.split() if normalized else []
