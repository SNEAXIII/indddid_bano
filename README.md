# BANO — recherche d'adresses floue, 100 % hors ligne

> **Synthèse du projet.** Recherche d'adresses françaises (Base Adresse
> Nationale Ouverte) directement sur le téléphone, **sans réseau, sans serveur,
> sans SQLite**. La solution finale retenue est un **moteur FST écrit en Rust**,
> embarqué dans une application Android via JNI.

---

## 1. Le problème

Chercher une adresse parmi **~2,2 millions** de voies françaises, en temps réel
à chaque frappe, alors que l'utilisateur :

- **tape vite et mal** : il faut tolérer les fautes de frappe (`beaugancy` →
  `Beaugency`) ;
- **ne met ni accents ni majuscules** : `paris`, `PARIS`, `Égalité` doivent tous
  fonctionner ;
- **tape par morceaux** : `bourg bress` doit déjà proposer *Bourg-en-Bresse* ;
- **n'a pas forcément de réseau** : tout doit tenir et tourner **sur l'appareil**.

Une base SQLite avec `LIKE`/FTS répond mal au *fuzzy* (fautes de frappe) et
grossit vite. Un service en ligne impose un réseau. D'où le besoin d'un moteur
**dédié, compact et offline**.

## 2. La démarche (et pourquoi le FST)

Le dépôt garde la trace de l'**exploration** qui a mené à la solution :

- `bench/v1` a comparé des **formats de stockage** (SQLite, Parquet, Arrow) ;
- `bench/v2` a comparé des **moteurs de recherche** (mesure latence / qualité).

⚠️ **`bench/` n'est que du défrichage de début de projet.** Aucune de ces pistes
n'a été livrée telle quelle : elles ont servi à **cadrer le problème et mesurer**.
Le produit (`demo/`) a été **conçu à part**, à la lumière de ces mesures.

La piste retenue : un **FST** (*Finite State Transducer*) interrogé par un
**automate de Levenshtein**. Ce couple donne, en une seule passe sur un
dictionnaire ultra-compact :

| Besoin | Réponse FST |
|---|---|
| Compacité | préfixes/suffixes communs partagés → **0,22 Mo pour 18 000 mots** |
| Fautes de frappe | **automate de Levenshtein** (distance 1 ou 2) en intersection avec le FST |
| Préfixe | automate `starts_with`, union avec le Levenshtein |
| Vitesse | lecture **mmap**, **~3 à 7 ms** par requête |

## 3. La solution livrée : `demo/`

```
demo/
├── rust/bano-fst/   Moteur FST : build l'index + recherche floue (CLI + pont JNI)
└── android/         App Android : la lib Rust embarquée, recherche à chaque frappe
```

### Comment marche une requête

```
 requête "bourg bress"
        │  normalize : minuscules, sans accents, ' et - → espaces
        ▼
 tokenise → ["bourg", "bress"]
        │  pour CHAQUE jeton :
        ▼
 union( préfixe ∪ automate de Levenshtein )  ──interroge──►  index.fst
        │                                                        │
        │   chaque mot trouvé → poids de similarité ∈ [0,1]      │
        │   (égal = 1 · préfixe = 0,9..1 · sinon 1 − dist/len)   │
        ▼                                                        ▼
 intersection ET : un enregistrement n'est gardé que s'il matche TOUS les jetons
        │  score = somme des meilleurs poids · tri (score ↓, rid ↑) · troncature
        ▼
 résultats : "voie | code_postal | ville" (accents d'origine restitués)
```

La **même** fonction `normalize`/`tokenize` est appliquée au **build** et à la
**requête** — d'où l'insensibilité naturelle aux accents et à la casse.

### L'artefact binaire (un dossier, lu en mmap)

Produit **une fois** par `build`, projeté en mémoire à chaque requête (ouverture
rapide, peu de RAM) :

| Fichier | Rôle |
|---|---|
| `index.fst` | dictionnaire trié des mots → `u64` empaqueté `(offset << 32) | len` |
| `postings.bin` | pour chaque mot, la liste des numéros d'adresses (`rid`, `u32`) |
| `records.bin` | données d'affichage : `voie \x01 cp \x01 ville` (accents conservés) |
| `vocab.bin` | miroir plat du FST lu par le moteur Java (voir parité ci-dessous) |

### Chiffres mesurés

| Échantillon **50 000 lignes** | Taille | | **France entière (~2,2 M adresses)** | Taille |
|---|---|---|---|---|
| `index.fst` | 0,22 Mo | | `index.fst` | 4 Mo |
| `postings.bin` | 1,17 Mo | | `postings.bin` | 51 Mo |
| `records.bin` | 1,95 Mo | | `records.bin` | 86 Mo |
| **Latence** | **~3 à 7 ms / requête** | | **APK final** | **~55 Mo** |

## 4. L'app Android (JNI)

À chaque frappe (debounce 80 ms), `BanoFst.java` appelle la lib Rust
`libbano_fst.so` **embarquée dans l'APK** via **JNI** (renvoie du JSON) — pas de
réseau, pas de SQLite, recherche *in-process*.

```
EditText ──frappe (debounce)──► BanoFst.search(q, 10)         [Java]
                                       │ JNI
                                       ▼
                  libbano_fst.so ──► Index::search() (mmap FST) [Rust]
                                       │
RecyclerView ◄── List<Result> ◄── JSON ┘
```

### Invariant : parité Rust ↔ Java

Le moteur existe en **deux implémentations qui doivent rendre des résultats
identiques** :

- **Rust** (`Index`, lit `index.fst`) — implémentation de référence ;
- **Java pur** (`PureIndex`, lit `vocab.bin`) — port mobile, sert à la mesure et
  à la parité (chemin de production = JNI vers Rust).

Même algorithme des deux côtés ; le test Rust `vocab_bin_matches_fst` garantit
que `vocab.bin` est bien le miroir du FST. Après optimisation, l'écart résiduel
est **structurel** (Rust ~×1,7 plus rapide en moyenne).

## 5. Lancer la démo

Tout passe par le **Makefile** racine (`make help` liste tout) — il gère les
spécificités Windows et le JDK Gradle.

```bash
# Données : télécharge le BANO national, extrait data/streets.csv (skip si présent)
make data

# Moteur Rust : compiler, construire l'index, chercher
make rust-build
make rust-index                                  # -> data/fst
make rust-search Q="bourg en bresse" LIMIT=5
make rust-search Q="beaugancy bourg"             # faute de frappe
make rust-search Q="allee beau"                  # préfixe

# Comprendre le moteur sur un mini-jeu de 5 lignes, traces [DEBUG] visibles
make sample-search-debug Q="bourg bres"

# App Android : build entièrement piloté par Gradle (aucune étape manuelle)
make android-debug                               # prepareData → generateBanoIndex → cargoBuild → APK
make android-install                             # installe sur l'appareil connecté
```

**Prérequis** : JDK 17, Android SDK + NDK, toolchain Rust (`cargo`), `uv`.

## 6. Carte du dépôt

```
./
├── demo/             ★ produit livré
│   ├── rust/bano-fst/  moteur FST (CLI + pont JNI)
│   ├── android/        app Android (Gradle compile la lib Rust + l'index)
│   └── animations/     explications animées Manim (grand public)
├── bench/            exploration de début (v1 = stockage · v2 = recherche) — non livré
├── dataprep/         outil Python : télécharge le BANO → data/streets.csv
├── data/             données hors git (full.csv.gz, streets.csv, fst/)
└── docs/             spécifications et plans
```
