# 📦 BANO Python Parser

> Projet de **benchmark et comparaison** de différentes stratégies pour parser et stocker les données du fichier CSV
> national [BANO](https://bano.openstreetmap.fr/) (Base Adresse Nationale Ouverte).

## 🎯 Objectif

Ce projet permet d'évaluer et comparer :

| Critère                   | Détail                                               |
|---------------------------|------------------------------------------------------|
| ⏱️ **Temps d'import**     | Mesure du temps de parsing CSV vers le format cible  |
| 📦 **Taille de stockage** | Comparaison de la taille finale des fichiers générés |
| 🔍 **Normalisation**      | Impact de la déduplication (3NF) vs données brutes   |
| 🗂️ **Format de sortie**  | SQLite (relationnel) vs Parquet (columnar)           |

---

## 📊 Stratégies comparées

### 💾 SQLite - DatabaseBuilder

| Builder                             | Approche                    | Nb Tables | ROWID | Avantage principal                         |
|-------------------------------------|-----------------------------|-----------|-------|--------------------------------------------|
| `BANODatabaseBuilderNoJoinsRowid`   | Table unique dénormalisée   | 1         | ✅     | Simplicité, requêtes simples               |
| `BANODatabaseBuilderNoJoinsWoRowid` | Table unique **sans ROWID** | 1         | ❌     | Taille réduite (~10-15%)                   |
| `BANODatabaseBuilderJoinsRowid`     | Normalisation 3NF complète  | 4         | ✅     | Déduplication max, intégrité référentielle |
| `BANODatabaseBuilderJoins2Rowid`    | Normalisation partielle     | 3         | ✅     | Compromis taille/complexité                |

#### 📐 Schémas de tables

**NoJoins** (1 table) :

```sql
adresses(nom_voie, code_postal, nom_commune)
```

**JoinsRowid** (4 tables - 3NF) :

```sql
voies(id, nom)
codes_postaux(id, code)
communes(id, nom)
adresses(id_nom_voie, id_code_postal, id_nom_commune)
```

**Joins2Rowid** (3 tables) :

```sql
codes_postaux(id, code)
communes(id, nom)
adresses(nom_voie, id_code_postal, id_nom_commune)  -- nom_voie non normalisé
```

### 📊 Parquet - ParquetBuilder

| Builder                    | Description                   | Déduplication | Avantage                              |
|----------------------------|-------------------------------|---------------|---------------------------------------|
| `BANOParquetBuilderSimple` | Fichier columnar (3 colonnes) | ✅ Optionnelle | Compression native, analytics rapides |

> **💡 Parquet** : Format optimisé pour la lecture analytique, avec compression Snappy/GZIP intégrée.

### ⚡ Arrow IPC - ArrowBuilder

| Builder                   | Description                   | Déduplication | Avantage                              |
|---------------------------|-------------------------------|---------------|---------------------------------------|
| `BANOArrowBuilderSimple`  | Fichier Arrow IPC (3 colonnes) | ✅ Optionnelle | Zero-copy, streaming, interopérabilité |

> **💡 Arrow IPC** : Format optimisé pour le transfert de données, zero-copy entre langages (Python ↔ Java/C++).

---

## 🏗️ Architecture

Le projet suit un **pattern Builder** avec héritage pour factoriser la logique commune.

```
bench/v1/
├── DatabaseBuilder/              # 💾 Builders SQLite
│   ├── Interface/
│   │   └── BANODatabaseBuilder.py      # Classe abstraite (gestion CSV, VACUUM, stats)
│   ├── BANODatabaseBuilderNoJoinsRowid.py
│   ├── BANODatabaseBuilderNoJoinsWoRowid.py
│   ├── BANODatabaseBuilderJoinsRowid.py
│   └── BANODatabaseBuilderJoins2Rowid.py
│
├── ParquetBuilder/               # 📊 Builders Parquet
│   ├── Interface/
│   │   └── BANOParquetBuilder.py       # Classe abstraite (PyArrow, streaming)
│   └── BANOParquetBuilderSimple.py
│
├── ArrowBuilder/                 # ⚡ Builders Arrow IPC
│   ├── Interface/
│   │   └── BANOArrowBuilder.py         # Classe abstraite (PyArrow IPC, streaming)
│   └── BANOArrowBuilderSimple.py
│
├── utils/
│   ├── DatabaseCursor.py         # Wrapper SQLite avec PRAGMAs optimisés
│   └── Perftime.py               # Décorateur @perf_time + PerfTimer context manager
│
├── streets.csv                   # 📂 CSV source (voie,cp,ville) produit par dataprep/
├── benchmark.py                  # 📊 Benchmark complet (SQLite + Parquet + Arrow)
└── pyproject.toml                # Configuration uv (pandas, pyarrow, duckdb)
```

### 🔑 Composants clés

| Composant             | Rôle                                                             |
|-----------------------|------------------------------------------------------------------|
| `BANODatabaseBuilder` | Classe abstraite gérant import CSV, batch commits, statistiques  |
| `BANOParquetBuilder`  | Classe abstraite avec streaming écriture Parquet + déduplication |
| `BANOArrowBuilder`    | Classe abstraite avec streaming écriture Arrow IPC + déduplication |
| `DatabaseCursor`      | Wrapper SQLite avec connexion optimisée (PRAGMAs, VACUUM)        |
| `@perf_time`          | Décorateur mesurant le temps d'exécution des méthodes            |

## 🔧 Installation

### Prérequis

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (gestionnaire de paquets rapide)

### Installation des dépendances

```bash
# 1) Installer uv (si nécessaire)
python3 -m pip install --user uv

# 2) Installer les dépendances
uv sync
```

## 🚀 Utilisation

### Générer une base SQLite

```bash
# Table unique simple (avec ROWID)
uv run python -m DatabaseBuilder.BANODatabaseBuilderNoJoinsRowid

# Table unique sans ROWID (optimisée en taille)
uv run python -m DatabaseBuilder.BANODatabaseBuilderNoJoinsWoRowid

# Tables normalisées avec jointures (3 tables de référence)
uv run python -m DatabaseBuilder.BANODatabaseBuilderJoinsRowid

# Tables semi-normalisées (2 tables de référence)
uv run python -m DatabaseBuilder.BANODatabaseBuilderJoins2Rowid
```

### Générer un fichier Parquet

```bash
# Parquet simple avec déduplication
uv run python -m ParquetBuilder.BANOParquetBuilderSimple
```

### Générer un fichier Arrow IPC

```bash
# Arrow IPC simple avec déduplication
uv run python -m ArrowBuilder.BANOArrowBuilderSimple
```

### 🏁 Exécuter les benchmarks

#### Benchmark complet (tous formats)

```bash
# Compare tous les fichiers générés (SQLite, Parquet, Arrow)
uv run python benchmark.py
```

Le benchmark affiche :
- 📦 **Taille des fichiers** avec ratio comparatif
- ⏱️ **Temps de lecture complète**
- 🔍 **Temps de recherche** (par code postal)
- 📈 **Temps d'agrégation** (COUNT DISTINCT)
- 📋 **Statistiques des données** (nombre d'adresses, voies, CP, communes)
- 🏆 **Résumé** avec le meilleur de chaque catégorie

## 📈 Métriques de performance

Chaque builder affiche automatiquement :

- ⏱️ **Temps d'import** (via le décorateur `@perf_time`)
- 📦 **Taille du fichier** avant/après optimisation
- 📊 **Statistiques** (nombre d'adresses, voies, codes postaux, communes)

### Optimisations SQLite appliquées

- `PRAGMA page_size = 4096` : Taille de page optimale
- `PRAGMA auto_vacuum = FULL` : Nettoyage automatique
- `PRAGMA journal_mode = WAL` : Write-Ahead Logging
- `PRAGMA temp_store = MEMORY` : Tables temporaires en RAM
- `VACUUM` + `ANALYZE` après import

## 📁 Fichiers générés

| Fichier                     | Builder              | Description                       |
|-----------------------------|----------------------|-----------------------------------|
| `bano_no_joins_rowid.db`    | NoJoinsRowid         | Table unique avec ROWID implicite |
| `bano_no_joins_wo_rowid.db` | NoJoinsWoRowid       | Table unique optimisée sans ROWID |
| `bano_joins_rowid.db`       | JoinsRowid           | 4 tables normalisées (3NF)        |
| `bano_joins2_rowid.db`      | Joins2Rowid          | 3 tables semi-normalisées         |
| `bano_simple.parquet`       | ParquetBuilderSimple | Fichier columnar compressé        |
| `bano_simple.arrow`         | ArrowBuilderSimple   | Fichier Arrow IPC streaming       |

---

## 📉 Résultats attendus

Exécutez tous les builders pour comparer :

| Stratégie        | Taille estimée | Temps estimé | Cas d'usage                                |
|------------------|----------------|--------------|--------------------------------------------|
| NoJoins          | ~200 Mo        | Rapide       | Requêtes simples, prototypage              |
| NoJoins WO ROWID | ~180 Mo        | Rapide       | Optimisation taille sur mobile             |
| Joins (3NF)      | ~150 Mo        | Moyen        | Intégrité référentielle, évite duplication |
| Joins2           | ~170 Mo        | Moyen        | Compromis entre simplicité et taille       |
| **Parquet**      | **~50 Mo**     | **Rapide**   | **Analytics, stockage long terme**         |
| **Arrow IPC**    | **~120 Mo**    | **Très rapide** | **Streaming, interopérabilité, Android** |

> ⚠️ **Note** : Les valeurs exactes dépendent du jeu de données BANO utilisé.

## 🗂️ Structure du CSV BANO

Le fichier `streets.csv` (produit par `dataprep/`, en-tête `voie,code_postal,ville`)
contient 3 colonnes, lues par index :

- **Colonne 0** : Nom de la voie
- **Colonne 1** : Code postal
- **Colonne 2** : Nom de la commune

## 📝 Exemples de code

### SQLite Builder

```python
from utils.DatabaseCursor import DatabaseCursor
from DatabaseBuilder.BANODatabaseBuilderNoJoinsRowid import BANODatabaseBuilderNoJoinsRowid

# Créer une connexion
cursor = DatabaseCursor("ma_base.db")

# Instancier le builder
builder = BANODatabaseBuilderNoJoinsRowid(cursor)

# Réinitialiser et importer
builder.reset_db()
builder.import_csv("streets.csv", batch_size=100000)

# Afficher les statistiques
builder.show_statistics()
```

### Parquet Builder

```python
from ParquetBuilder.BANOParquetBuilderSimple import BANOParquetBuilderSimple

# Instancier le builder
builder = BANOParquetBuilderSimple("ma_base.parquet")

# Réinitialiser et importer avec déduplication
builder.reset_file()
builder.import_csv(
    "streets.csv",
    batch_size=100000,
    deduplicate=True,  # Active la déduplication
    print_duplicates=True,  # Affiche les doublons détectés
)

# Afficher les statistiques
builder.show_statistics()
```

## 📜 Licence

Projet interne AFC.
