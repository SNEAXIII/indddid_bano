# search_bench/queryset/generate.py
"""Génère un jeu de requêtes labellisées (reproductible via seed)."""

import json
import random

from search_bench.data import Record, load_records


def _make_prefix(rng: random.Random, text: str) -> str:
    cut = max(2, int(len(text) * rng.uniform(0.4, 0.8)))
    return text[:cut].strip()


def _make_typo(rng: random.Random, text: str) -> str:
    chars = list(text)
    idxs = [i for i, c in enumerate(chars) if c != " "]
    if len(idxs) < 2:
        return text
    op = rng.choice(["delete", "substitute", "transpose"])
    i = rng.choice(idxs)
    if op == "delete":
        del chars[i]
    elif op == "substitute":
        chars[i] = rng.choice("abcdefghijklmnopqrstuvwxyz")
    else:
        j = min(i + 1, len(chars) - 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def _make_shuffle(rng: random.Random, text: str) -> str:
    words = text.split()
    rng.shuffle(words)
    return " ".join(words)


def generate_balanced(
    records: list[Record],
    per_word_count: int,
    max_words: int,
    seed: int,
) -> list[dict]:
    """Jeu équilibré : >= `per_word_count` requêtes pour CHAQUE nombre de mots 1..max_words.

    Pour chaque w, on prend des adresses ayant >= w mots et on fabrique une requête
    de EXACTEMENT w mots à partir des w premiers mots normalisés (préfixe réaliste),
    puis on alterne les variantes (préfixe / typo / mélange) qui conservent le nb de mots.
    La cible reste l'adresse complète (voie, cp, ville).
    """
    rng = random.Random(seed)
    out: list[dict] = []
    seen: set[str] = set()

    for w in range(1, max_words + 1):
        candidates = [r for r in records if len(r.search_text.split()) >= w]
        rng.shuffle(candidates)
        kinds = ("prefix", "typo") if w == 1 else ("prefix", "typo", "shuffle")
        produced = 0
        ci = 0
        for rec in candidates:
            if produced >= per_word_count:
                break
            base = " ".join(rec.search_text.split()[:w])
            kind = kinds[ci % len(kinds)]
            if kind == "prefix":
                query = base
            elif kind == "typo":
                query = _make_typo(rng, base)
            else:
                query = _make_shuffle(rng, base)
            ci += 1
            query = query.strip()
            if not query or len(query.split()) != w or query in seen:
                continue
            seen.add(query)
            out.append(
                {
                    "query": query,
                    "kind": kind,
                    "words": w,
                    "target": {
                        "voie": rec.voie,
                        "code_postal": rec.code_postal,
                        "ville": rec.ville,
                    },
                }
            )
            produced += 1
    return out


def generate_queries(records: list[Record], n_targets: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    targets = rng.sample(records, min(n_targets, len(records)))
    out: list[dict] = []
    for rec in targets:
        base = rec.search_text
        for kind, fn in (
            ("prefix", _make_prefix),
            ("typo", _make_typo),
            ("shuffle", _make_shuffle),
        ):
            query = fn(rng, base)
            if not query.strip():
                continue
            out.append(
                {
                    "query": query,
                    "kind": kind,
                    "target": {
                        "voie": rec.voie,
                        "code_postal": rec.code_postal,
                        "ville": rec.ville,
                    },
                }
            )
    return out


def main() -> None:
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Génère shared/queries.json")
    parser.add_argument("-i", "--input", default="../../data/streets.csv")
    parser.add_argument("-o", "--output", default="shared/queries.json")
    parser.add_argument("-n", "--n-targets", type=int, default=2000)
    parser.add_argument("-s", "--seed", type=int, default=42)
    parser.add_argument(
        "-m",
        "--max-records",
        type=int,
        default=None,
        help="limite le nombre de lignes chargées (défaut : tout)",
    )
    parser.add_argument(
        "--balanced",
        action="store_true",
        help="jeu équilibré : >= --per-word-count requêtes par nb de mots 1..--max-words",
    )
    parser.add_argument(
        "--per-word-count",
        type=int,
        default=20,
        help="min de requêtes par nombre de mots (mode --balanced)",
    )
    parser.add_argument(
        "--max-words",
        type=int,
        default=9,
        help="nombre de mots max couvert (mode --balanced)",
    )
    args = parser.parse_args()

    records = load_records(args.input, limit=args.max_records)
    if args.balanced:
        queries = generate_balanced(
            records,
            per_word_count=args.per_word_count,
            max_words=args.max_words,
            seed=args.seed,
        )
    else:
        queries = generate_queries(records, n_targets=args.n_targets, seed=args.seed)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
    print(f"✓ {len(queries)} requêtes écrites dans {args.output}")


if __name__ == "__main__":
    main()
