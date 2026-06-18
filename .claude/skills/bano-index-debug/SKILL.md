---
name: bano-index-debug
description: >-
  Débogue et inspecte l'index de recherche d'adresses BANO (moteur Rust
  bano-fst + moteur Java PureIndex) : structure FST, vocab.bin, postings.bin,
  records.bin, tokenisation, scoring Levenshtein, intersection ET. Utilise cette
  skill dès que l'utilisateur enquête sur un résultat de recherche bizarre,
  manquant, mal classé ou différent entre Rust et Java, OU qu'il dit « pourquoi
  cette adresse ne sort pas », « pourquoi ce score », « inspecte l'index »,
  « dump le FST / les postings », « quels jetons », « trace la recherche »,
  « Rust et Java ne donnent pas pareil », « BANO_DEBUG », même sans nommer un
  fichier précis. Vaut aussi pour vérifier la cohérence d'un index reconstruit.
---

# Débogage de l'index BANO

Le moteur cherche des adresses françaises en flou (fuzzy) sur un artefact
binaire. Deux implémentations qui DOIVENT donner les mêmes résultats :
- **Rust** (`demo/rust/bano-fst/src/index.rs`) — référence, lit `index.fst`.
- **Java** (`demo/android/.../pure/PureIndex.java`) — port mobile, lit `vocab.bin`.

Un bug se range presque toujours dans une de ces 4 couches. Débogue dans cet
ordre — chaque couche suppose la précédente correcte :

1. **Tokenisation** — la requête (et les adresses au build) deviennent quels jetons ?
2. **Match FST** — quels jetons du vocab matchent (préfixe ∪ Levenshtein) ?
3. **Postings** — quels records (rid) chaque jeton touche ?
4. **Scoring / intersection ET** — somme des poids, tri (score desc, rid asc), troncature.

## Couche 0 : reproduire avec les traces

Le moteur Rust imprime des traces `[DEBUG]` à CHAQUE couche quand `BANO_DEBUG`
est défini. C'est le premier réflexe : ça montre tokens → distance Levenshtein
par jeton → chaque match FST avec son poids → nb records par jeton → survivants
de l'intersection → top trié. Cibles Make (depuis la racine) :

```bash
make sample-search-debug Q="bourg bres"   # mini-jeu 5 lignes, traces ON
make rust-search Q="rue de la paix" DEBUG=1 LIMIT=5   # index complet (data/fst)
```

Le mini-jeu (`demo/rust/bano-fst/sample5.csv` → `sample5_index`) est l'outil
idéal pour isoler un comportement : 5 lignes, sortie lisible. `make sample-index`
le (re)construit.

Lis la trace de haut en bas et trouve la PREMIÈRE couche où la réalité diverge
de l'attendu. Inutile de déboguer le scoring si le jeton ne matche même pas.

## Couche binaire : inspecter sans le moteur

Quand les traces ne suffisent pas (ou pour vérifier ce que le moteur voit
vraiment), décode l'artefact directement avec le script fourni. `index.fst` est
opaque en dehors de Rust, mais `vocab.bin` porte les MÊMES jetons et valeurs
`packed` (garanti par le test `vocab_bin_matches_fst` de build.rs) — et c'est
exactement ce que lit le Java. Inspecter `vocab.bin`, c'est inspecter le FST.

```bash
DIR=demo/rust/bano-fst/sample5_index   # ou data/fst, ou bench/v2/shared/artifacts/...
python .claude/skills/bano-index-debug/scripts/inspect_index.py $DIR stats
python .claude/skills/bano-index-debug/scripts/inspect_index.py $DIR token bourg
python .claude/skills/bano-index-debug/scripts/inspect_index.py $DIR grep bres
python .claude/skills/bano-index-debug/scripts/inspect_index.py $DIR record 3
python .claude/skills/bano-index-debug/scripts/inspect_index.py $DIR check
```

- `token <jeton>` répond direct à « pourquoi telle adresse (ne) sort (pas) ? » :
  recherche EXACTE du jeton, liste ses rid, résout chaque rid en adresse. Si le
  jeton attendu est absent, le problème est en amont (tokenisation au build).
- `grep <sous-chaine>` trouve les variantes proches (utile quand un accent ou
  une coupure a produit un jeton inattendu).
- `check` valide la cohérence (vocab trié par octets, Σ len == postings, rid en
  bornes) — à lancer après toute reconstruction d'index.

Le détail des formats binaires (octet par octet) est dans
`references/binary-formats.md` — lis-le seulement si tu dois écrire un nouveau
décodeur ou modifier `build.rs`.

## Couche parité Rust ↔ Java

Quand « Rust et Java ne donnent pas pareil », l'algorithme est censé être
identique (même union préfixe ∪ Levenshtein, même intersection ET, même tri
score desc / rid asc, mêmes poids `similarity`). Les écarts viennent presque
toujours de :

- **Tokenisation divergente** : compare `normalize.rs::tokenize` (Rust) et
  `Normalize.tokenize` (Java) sur la requête litigieuse. Même requête → mêmes
  jetons, sinon tout diverge.
- **Distance Levenshtein par jeton** : `d = 1` si le jeton fait ≤ 4 caractères,
  sinon `d = 2` — dans les DEUX moteurs (`qtok.chars().count()` côté Rust,
  `codePointCount` côté Java). Un écart de comptage de caractères (accents,
  codepoints) change `d` et donc les matchs.
- **Poids `similarity`** : égal=1.0, préfixe=0.9+0.1·ratio, sinon
  1−dist/maxlen. Identique des deux côtés ; vérifie-le si un score diffère.

Le Java a en plus un mécanisme de **deadline** (`TimeoutException`) absent du
Rust : une requête qui « ne rend rien » côté Java peut simplement avoir dépassé
l'échéance. Le Rust n'a pas cette limite.

## Build & environnement

- Reconstruire l'index complet : `make rust-index` (lit `data/streets.csv` →
  `data/fst`). Mini-jeu : `make sample-index`.
- Tests Rust (incluent la parité vocab/FST et index/search) : `make rust-test`.
- Gradle (build Java/Android) plante avec le `JAVA_HOME` par défaut sur cette
  machine (JBR cassé) — le Makefile force `Android Studio1/jbr`. Si tu lances
  gradle à la main, utilise ce JDK. Voir la mémoire projet `jdk-java-home-quirk`.

## Méthode

Ne devine pas : reproduis avec `BANO_DEBUG`, lis la trace couche par couche,
confirme avec l'inspecteur binaire sur le jeton/record précis, et seulement
alors propose une cause. Le mini-jeu 5 lignes est ton ami pour tout isoler.
