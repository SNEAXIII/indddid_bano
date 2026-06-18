# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Vue d'ensemble

Recherche floue d'adresses françaises (BANO) **100 % hors ligne**. Tout
consomme un CSV partagé `data/streets.csv` produit par `dataprep/`.

```
demo/     ⭐ LE PRODUIT — c'est ici que se fait le vrai travail : rust/bano-fst (moteur FST) + android (app, lib Rust via JNI)
bench/    recherches infructueuses du début (v1 = stockage ; v2 = recherche) — impasses, voir plus bas
dataprep/ télécharge le BANO national et extrait data/streets.csv
data/     hors git (volumineux, régénérable) : full.csv.gz, streets.csv, fst/
demo/animations/  explications Manim grand public (voir skill manim-explainer)
```

**`bench/` ne compte pas — ce sont des recherches infructueuses du début.**
Aucune des pistes (v1 stockage, v2 recherche) n'a été retenue ; c'était du
défrichage pour cadrer le problème, pas du code livré. Ne travaille PAS dans
`bench/` sauf demande explicite : tout l'effort va dans `demo/`, dont le moteur
FST a été conçu à part, à la lumière de ces mesures. Ne traite jamais `bench/`
comme la base de `demo/` et ne « branche » rien de l'un sur l'autre. Les README
de `bench/` sont peu fiables (chemins morts, « moteur retenu » trompeur) : à
lire comme notes de recherche, pas comme doc du produit.

`data/` n'est **jamais** committé.

## Le Makefile est l'interface

Tout passe par le `Makefile` racine (`make help` liste tout). Il gère les
spécificités Windows (force le bash de Git), le suffixe `.exe`, et le JDK Gradle.
Préfère les cibles Make aux commandes brutes — les README des sous-dossiers
peuvent être en retard sur le Makefile (chemins/cibles renommés).

```bash
make data                       # dataprep -> data/streets.csv (skip si présent)
make rust-build / rust-test     # compile / teste le moteur Rust
make rust-index                 # construit l'index FST complet -> data/fst
make rust-search Q="..." [DEBUG=1] [LIMIT=5]
make sample-index               # mini-index 5 lignes (sample5.csv -> sample5_index)
make sample-search-debug Q="..."  # recherche sur le mini-jeu, traces [DEBUG] ON
make android-so / android-index / android-debug / android-install
make v2-test                    # pytest du banc d'essai v2
```

Un seul test Rust : `cd demo/rust/bano-fst && cargo test --release <nom_du_test>`.
Un seul test pytest : `cd bench/v2 && uv run pytest -q -k <expr>`.

## Invariant central : parité Rust ↔ Java

Le moteur existe en **deux implémentations qui doivent rendre des résultats
identiques** :
- **Rust** `demo/rust/bano-fst/src/index.rs` — référence, lit `index.fst`.
- **Java** `demo/android/.../pure/PureIndex.java` — port mobile, lit `vocab.bin`.

Même algorithme des deux côtés : par jeton de requête, union(préfixe ∪ automate
de Levenshtein, distance 1 si ≤ 4 caractères sinon 2), poids `similarity` ∈ [0,1]
(égal=1 ; préfixe=0,9+0,1·ratio ; sinon 1−dist/maxlen), **intersection ET** en
sommant les poids, tri (score desc, rid asc), troncature. Toute modif d'un côté
doit être répliquée de l'autre. Le Java a en plus une **deadline**
(`TimeoutException`) absente du Rust. Pour déboguer un écart ou un résultat
inattendu, utilise la skill **bano-index-debug**.

## L'artefact binaire (un dossier, 4 fichiers)

Produit une fois par `build` (Rust), lu en **mmap** à chaque requête. La même
fonction `normalize`/`tokenize` est appliquée au build ET à la requête (d'où
l'insensibilité accents/casse). Détail octet par octet :
`.claude/skills/bano-index-debug/references/binary-formats.md`.

- `index.fst` — `fst::Map` : jeton → `u64` packed `(offset_postings_en_u32 << 32) | len`. Clés insérées en ordre **croissant des octets** (le build trie).
- `vocab.bin` — miroir plat du FST lu par le Java (mêmes jetons + packed, garanti par le test Rust `vocab_bin_matches_fst`).
- `postings.bin` — concaténation de `u32` (les rid), par jeton dans l'ordre trié.
- `records.bin` — `u32 n | (n+1) offsets | blob` ; record = `voie \x01 cp \x01 ville` (accents d'origine conservés).

## App Android (JNI)

À chaque frappe (debounce), `BanoFst.java` appelle la lib Rust `libbano_fst.so`
via JNI (`jni_bridge.rs`, feature `jni`, renvoie du JSON) — pas Panama/FFM
(indisponible sur ART). Le moteur **PureIndex** (Java pur, sans Rust) est une
seconde implémentation servant à la mesure et à la parité, pas au chemin JNI.
Build piloté par Gradle : `prepareData` → `generateBanoIndex` → `cargoBuild`.

## Environnements & pièges

- Chaque sous-projet Python (`dataprep`, `bench/v1`, `bench/v2`) a son env **uv**
  isolé (`uv sync` puis `uv run …`). Lance toujours les commandes Python via `uv run`.
- **Gradle / JAVA_HOME** : le `JAVA_HOME` par défaut de cette machine pointe un
  JBR cassé → le CLI gradle plante. Le Makefile force `Android Studio1/jbr`
  (`GRADLE_JDK`). Si tu lances gradle à la main, utilise ce JDK. Voir la mémoire
  projet `jdk-java-home-quirk`.
- Bench Rust vs Java : après optimisation du moteur Java, l'écart résiduel est
  structurel (×1,7 moyen en faveur du Rust). Voir mémoire `bench-rust-vs-java-gap`.
- Le projet est francophone (code, commentaires, commits) — garde cette langue.
