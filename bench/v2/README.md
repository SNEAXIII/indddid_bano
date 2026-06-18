# 🔎 BANO Search Bench — Guide d'utilisation

Banc d'essai **desktop (Python)** pour comparer des méthodes de **recherche / autocomplétion offline**
sur les adresses BANO (triplets `voie, code_postal, ville`). Il mesure latence, taille et qualité
(recall@k, MRR) de chaque méthode, puis sélectionne les **survivantes** à porter ensuite sur Android.

## ⚙️ Prérequis

- Python ≥ 3.10
- [uv](https://github.com/astral-sh/uv)
- Un fichier `streets.csv` à l'entête `voie,code_postal,ville` (produit par
  `utils/ExtractUniqueAddresses.py` à partir du fichier national BANO).

## 📦 Installation

```bash
cd new/desktop
uv sync          # crée .venv + installe pyarrow et pytest
```

## 🚀 Utilisation en 3 étapes

> ⚠️ **Règle d'or :** le jeu de requêtes **doit** être généré depuis le **même** `streets.csv` que
> celui passé au benchmark. Sinon les cibles n'existent pas dans les données testées et le
> **recall vaut 0 partout**.

### 1. Générer le jeu de requêtes

```bash
uv run python -m search_bench.queryset.generate \
    -i /chemin/vers/streets.csv \
    -o ../shared/queries.json \
    -n 2000 \
    -s 42
```

| Option | Défaut | Rôle |
|---|---|---|
| `-i, --input` | `../streets.csv` | CSV source |
| `-o, --output` | `../shared/queries.json` | Jeu de requêtes labellisé |
| `-n, --n-targets` | `2000` | Nb d'adresses cibles échantillonnées |
| `-s, --seed` | `42` | Graine (reproductible) |

Chaque cible génère **3 requêtes** : `prefix` (saisie en cours), `typo` (faute injectée),
`shuffle` (mots dans le désordre). Avec `-n 2000` → **6000 requêtes**.

### 2. Lancer le benchmark

```bash
uv run python -m search_bench.bench.run \
    -i /chemin/vers/streets.csv \
    -q ../shared/queries.json \
    -o reports \
    --limit 10
```

| Option | Défaut | Rôle |
|---|---|---|
| `-i, --input` | `../streets.csv` | CSV source (le même qu'à l'étape 1) |
| `-q, --queries` | `../shared/queries.json` | Jeu de requêtes |
| `-o, --out-dir` | `reports` | Dossier de sortie |
| `--limit` | `10` | Nb de résultats par requête |

> 💡 Dans un terminal, la progression (`→ csv_scan ...`) s'affiche en direct. Si tu **rediriges**
> la sortie vers un fichier ou un pipe (ex : run en tâche de fond `> run.log`), stdout devient
> bufferisé et rien n'apparaît avant la fin : ajoute alors `-u` (`uv run python -u -m ...`) ou
> `PYTHONUNBUFFERED=1`.

### 3. Lire le rapport

Deux fichiers dans `reports/` :
- `report.md` — tableau lisible (ci-dessous)
- `report.json` — `{"reports": [...], "survivors": [...]}` pour traitement automatisé

## ♻️ Prebuild & export Android

Construire les index est coûteux (25-30 s/moteur à 2 M). Le **prebuild** les construit une fois ;
le benchmark les **recharge** ensuite (mesure un `load ms` de cold-start distinct du build).

> ⚠️ Le prebuild accélère le **build**, pas la **latence requête** des méthodes en O(N)
> (csv/parquet/arrow/inverted/trigram_levenshtein restent lents par requête à grande échelle).

```bash
# 1. Construire tous les artefacts une fois (shared/artifacts/<moteur>/ + manifest.json)
uv run python -m search_bench.prebuild -i ./streets.csv -o ../shared/artifacts

# 2. Benchmarker en RECHARGEANT les artefacts (load au lieu de build)
uv run python -m search_bench.bench.run --artifacts ../shared/artifacts -q ../shared/queries.json -o reports

# 3. Exporter les survivantes en SQLite Android (lit reports/report.json -> survivors)
uv run python -m search_bench.export_android -a ../shared/artifacts -r reports/report.json -o ../shared/android
#    ou survivantes explicites :
uv run python -m search_bench.export_android -a ../shared/artifacts -s fts5_trigram inverted_index -o ../shared/android
```

Formats d'artefact : `parquet`/`arrow`/`db` natifs, index en RAM en `pickle` (desktop). L'export
Android réécrit chaque survivante en **SQLite** (`.db`) : FTS/LIKE copiés tels quels ; index →
table `records` + table `tokens(token, postings BLOB int32)`. Ces `.db` se copient directement
dans `android/assets/`.

## 🗺️ Ce qui se passe dans le code

### Générateur de requêtes (`search_bench/queryset/generate.py`)

```
streets.csv  (voie,code_postal,ville)
   │  load_records()                       → ignore les lignes sans voie/ville
   ▼
list[Record]   chaque Record met en cache .search_text + .tokens (normalisés)
   │  generate_queries(records, n_targets, seed)
   ▼
rng = random.Random(seed)                  ← graine fixe = reproductible
targets = rng.sample(records, n_targets)   ← N adresses cibles
   │
   │  pour chaque cible : 3 variantes de son search_text, label = la cible
   ▼
 ┌───────────────┬─────────────────────────┬──────────────────────────┐
 │ prefix        │ typo                    │ shuffle                  │
 │ coupe 40–80 % │ 1 faute injectée :      │ mots dans le désordre    │
 │ "rue de la p" │ suppr / subst / transpo │ "paris … paix"           │
 └───────────────┴─────────────────────────┴──────────────────────────┘
   │  {query, kind, target:{voie, code_postal, ville}}
   ▼
shared/queries.json   =   liste de N × 3 requêtes labellisées
```

### Run benchmark (`search_bench/bench/run.py`)

```
streets.csv ──load_records()──► records          queries.json ──► queries
                                   │                                  │
                                   └──────────────┬───────────────────┘
                                                  ▼
                       pour chaque moteur de ENGINES (9) :
   ┌──────────────────────────────────────────────────────────────────┐
   │ engine = Cls()                                                     │
   │ engine.build(records)              ⏱ build_time_ms  📦 artifact   │
   │ pour chaque query :                                                │
   │    t0 ; results = engine.search(query, limit) ; latence = now-t0   │
   │    recall@5 / recall@10 / RR   ←  results vs query["target"]       │
   │ engine.close()                     (finally : libère la connexion) │
   └──────────────────────────────────────────────────────────────────┘
                                                  │  agrégation
                                                  ▼
        report = { p50/p95/p99 (percentiles des latences),
                   build_ms, taille, recall@5, recall@10, MRR }
                                                  │
        select_survivors(recall@5 ≥ 0.5  ET  p95 ≤ 50 ms)
                                                  ▼
                       reports/report.json   +   reports/report.md
```

## 🧪 Méthodes comparées

| Méthode | fuzzy | Principe |
|---|:---:|---|
| `csv_scan` | ✅ | Scan linéaire en mémoire + scoring fuzzy (référence qualité) |
| `parquet_scan` | ✅ | Idem, source colonnaire Parquet (mesure le coût round-trip) |
| `arrow_scan` | ✅ | Idem, source Arrow IPC |
| `trie_prefix` | — | Trie de préfixes en mémoire (pas de tolérance aux fautes) |
| `inverted_index` | ✅ | Postings par token + expansion trigrammes |
| `trigram_levenshtein` | ✅ | Candidats par trigrammes + re-classement Levenshtein |
| `like` | — | SQLite `LIKE '%x%'` ANDé (témoin naïf) |
| `fts5_unicode61` | — | SQLite FTS5, tokens + préfixe, diacritiques retirés |
| `fts5_trigram` | ✅* | SQLite FTS5 tokenizer trigram (sous-chaînes) |

*`fts5_trigram` ne tolère que les fautes **préservant un trigramme complet** → marqué non-fuzzy
dans les tests de contrat.*

## 📊 Métriques

- **p50 / p95 / p99 (ms)** — latence requête (warm)
- **build ms** — temps de construction de l'index
- **taille** — artefact sur disque (`mémoire` si purement en RAM)
- **recall@5 / recall@10** — la cible est-elle dans le top-k
- **MRR** — Mean Reciprocal Rank (1/rang de la cible)

## 🏁 Triage (survivantes)

`select_survivors` retient une méthode si `recall@5 ≥ 0.5` **ET** `p95 ≤ 50 ms`
(seuils ajustables dans `search_bench/bench/run.py`).

## ✅ Tests

```bash
uv run pytest -q        # 57 tests (normalisation, scoring, 9 moteurs, métriques, harness)
```

## 📈 Résultats de référence (France entière, 2,2 M adresses, 60 requêtes)

| Méthode | p50 | p95 | taille | recall@5 |
|---|---|---|---|---|
| `trie_prefix` | 0,16 ms | 34 ms | mémoire | 0,57 |
| `fts5_trigram` | 49 ms | 158 ms | 364 Mo | 0,65 |
| `fts5_unicode61` | 132 ms | 517 ms | 172 Mo | 0,60 |
| `like` | 215 ms | 282 ms | 101 Mo | 0,62 |
| `csv` / `parquet` / `arrow` scan | ~73 s | ~105 s | — | **0,78** |
| `inverted_index` | 67 s | 90 s | mémoire | 0,78 |
| `trigram_levenshtein` | 69 s | 90 s | mémoire | 0,78 |

**Lecture :** les scans fuzzy donnent la meilleure qualité (0,78) mais sont **inutilisables**
(~70 s/requête). `trie_prefix` et les FTS5 sont rapides mais limités sur les fautes de frappe.

## ⚠️ Limites connues / à venir

- **Fuzzy non scalable** : `inverted_index` et `trigram_levenshtein` sont aussi lents que le scan
  complet (union de candidats non bornée). À corriger (candidats bornés par trigrammes partagés +
  intersection par token) pour viser fuzzy + p95 < 150 ms à 2 M.
- **Benchmark lent** : un run complet sur 2 M lignes prend ~40 min à cause des moteurs en O(N).
  Une option `--sample N` et l'exclusion des scans des runs complets sont prévues.
- **Taille mobile** : `fts5_trigram` pèse 364 Mo sur 2 M — à surveiller pour l'embarqué Android.
