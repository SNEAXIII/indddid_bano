uv run python -m search_bench.bench.run -i ./streets.csv -q ../shared/queries.json -o reports --limit 10

uv run python -m search_bench.queryset.generate -i ./streets.csv -o ../shared/queries.json -n 2000 -s 42

# --- Prebuild (construit les 9 artefacts UNE fois + manifest.json) ---
uv run python -m search_bench.prebuild -i ./streets.csv -o ../shared/artifacts

# --- Benchmark en RECHARGEANT les artefacts (load au lieu de build, affichage live) ---
uv run python -m search_bench.bench.run --artifacts ../shared/artifacts -q ../shared/queries.json -o reports --limit 10

# --- Export Android des survivantes (lit reports/report.json -> survivors) ---
uv run python -m search_bench.export_android -a ../shared/artifacts -r reports/report.json -o ../shared/android

Côté Android offline
- « Android SQLite FTS search » / « Room full text search » — pour la partie embarquée.

Mon conseil d'ordre de visionnage, pour que ça matche notre archi :
1. Levenshtein (la base du scoring)
2. Inverted index + trigrammes (génération de candidats)
3. Autocomplete/typeahead system design (vue d'ensemble : trie, ranking, top-k)
4. SQLite FTS5 (l'implémentation concrète qu'on benchmarke)

Si tu me dis quel point est le plus flou pour toi (le scoring fuzzy ? l'indexation ? le FTS5 ?), je peux te faire un mini-schéma maison
sur celui-là, sans dépendre d'une vidéo.