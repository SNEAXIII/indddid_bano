# Bench — bancs d'essai de recherche d'adresses

Deux générations d'exploration, chacune avec son environnement `uv` isolé. Toutes
deux consomment `../data/streets.csv` (voir `dataprep/` à la racine).

## v1 — première génération

Builders d'index expérimentaux et harnais historique :

- `ArrowBuilder/`, `ParquetBuilder/` — stockage colonnaire.
- `DatabaseBuilder/` — variantes SQLite (joins / rowid / FTS).
- `DemoParser/` — prototype de parseur d'adresses.
- `benchmark.py` — point d'entrée de mesure.

```bash
cd bench/v1 && uv sync && uv run python benchmark.py
```

## v2 — seconde génération (`search_bench`)

Banc d'essai structuré : moteurs interchangeables + métriques + jeu de requêtes
labellisé reproductible.

- `search_bench/engines/` — moteurs comparés (FTS5, trigram, inverted index, trie…).
- `search_bench/bench/` — exécution et scoring.
- `search_bench/queryset/` — génération du jeu de requêtes.
- `shared/queries.json` — jeu de requêtes reproductible (committé).

```bash
cd bench/v2
uv sync
uv run pytest -q
uv run python -m search_bench.queryset.generate     # -> shared/queries.json
uv run python -m search_bench.prebuild              # -> shared/artifacts/
uv run python -m search_bench.bench.run --artifacts shared/artifacts
```

Le moteur retenu (FST) est ré-implémenté en Rust dans `demo/rust/bano-fst`.
