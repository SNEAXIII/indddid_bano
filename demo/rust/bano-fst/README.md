# bano-fst — recherche d'adresses floue, hors ligne

`bano-fst` est un petit programme en ligne de commande (Rust) qui permet de
**rechercher une adresse** dans un gros fichier d'adresses BANO
(`voie,code_postal,ville`), **sans connexion réseau** et de manière très rapide.

Il gère :

- **l'insensibilité aux accents et à la casse** : `PARIS`, `Paris`, `paris`
  donnent le même résultat ; `Égalité` est traité comme `egalite` ;
- **les fautes de frappe** (recherche « floue » / *fuzzy*), via un **automate de
  Levenshtein** : `beaugancy` retrouve `Beaugency` ;
- **la recherche par préfixe** : `beau` retrouve `Beaulieu`, `Beautor`, etc. ;
- une **recherche multi-mots en ET** : `bourg bresse` ne garde que les
  enregistrements contenant les deux mots.

Tout repose sur un **artefact binaire compact** (3 fichiers) produit une fois à
partir du CSV, puis lu en *memory-map* (mmap) à chaque requête.

---

## 1. Compiler

Pré-requis : [Rust / Cargo](https://rustup.rs) installé.

```bash
cargo build --release
```

Le premier build télécharge et compile les dépendances (FST, csv, memmap2,
unicode-normalization) — quelques minutes la première fois, c'est normal.
Le binaire est ensuite dans `target/release/bano-fst`.

---

## 2. Utiliser

### a) Construire l'index (une seule fois)

```bash
./target/release/bano-fst build <streets.csv> <dossier_sortie>
```

Exemple :

```bash
./target/release/bano-fst build streets.csv ./index
```

Cela écrit 3 fichiers dans `./index/` : `index.fst`, `postings.bin`,
`records.bin` (voir le format plus bas). Le programme affiche le nombre
d'enregistrements, le nombre de jetons uniques et la taille des 3 fichiers.

### b) Rechercher

```bash
./target/release/bano-fst search <dossier_index> "<requête>" [limite]
```

`limite` est optionnel (10 par défaut). Exemples :

```bash
./target/release/bano-fst search ./index "bourg en bresse" 5
./target/release/bano-fst search ./index "BOURG-EN-BRESSE" 5     # majuscules + tirets
./target/release/bano-fst search ./index "beaugancy bourg" 5     # faute de frappe
./target/release/bano-fst search ./index "allee beau" 5          # préfixe
```

Chaque résultat s'affiche ainsi (le score est la somme des similarités par mot,
plus il est haut mieux c'est) :

```
score   voie | code_postal | ville
```

Le temps de réponse (latence) est affiché en fin de sortie.

---

## 3. Format de l'artefact binaire (3 fichiers)

L'index est volontairement découpé en 3 fichiers complémentaires :

```
 index.fst    le DICTIONNAIRE trié des mots -> où trouver leurs adresses
 postings.bin pour chaque mot, la LISTE des numéros d'adresses (rid)
 records.bin  les DONNÉES D'AFFICHAGE (voie/cp/ville d'origine, avec accents)
```

Schéma de la chaîne mot → adresses :

```
 requête "bourg"
       │  (recherche dans le FST, accents/casse déjà normalisés)
       ▼
 index.fst :  "bourg" ─► valeur u64 empaquetée = (offset << 32) | len
       │                         │            │
       │            offset (en u32) ┘            └ len (nb de rid)
       ▼
 postings.bin : [ ... | rid, rid, rid, ... | ... ]
                       └ tranche [offset .. offset+len]
       │  (chaque rid = numéro de ligne du CSV)
       ▼
 records.bin :  rid ─► "voie \x01 code_postal \x01 ville"
```

### `index.fst` — un `fst::Map`

Un **FST** (*Finite State Transducer*) est ici utilisé comme un dictionnaire
trié extrêmement compact qui associe **une clé** (un mot normalisé, en octets)
à **une valeur `u64`**. Les clés étant partagées au niveau des préfixes/suffixes
communs, le fichier est petit (≈ 0,2 Mo pour 18 000 mots).

La valeur `u64` **empaquette deux nombres** pour localiser la liste de postings :

```
valeur = (offset as u64) << 32 | (len as u64)
         └ bits 63..32 : offset (en unités u32) dans postings.bin
                         └ bits 31..0 : len = nombre de rid pour ce mot
```

À la lecture : `offset = valeur >> 32` et `len = valeur & 0xFFFF_FFFF`.

> ⚠️ Les clés d'un FST **doivent être insérées dans l'ordre croissant des
> octets**. C'est pourquoi le build trie les mots avant de les insérer.

### `postings.bin` — les listes de numéros d'adresses

Une simple concaténation de `u32` *little-endian* : pour chaque mot (dans le
même ordre trié que le FST), ses rid à la suite. Les rid du mot `T` sont la
tranche `postings[offset .. offset+len]`.

### `records.bin` — les données d'affichage

```
 [ u32 n ]                         nombre d'enregistrements
 [ (n+1) × u32 offsets ]           positions dans le blob (le dernier = taille du blob)
 [ blob ]                          "voie \x01 cp \x01 ville" pour chaque enregistrement
```

L'enregistrement `i` correspond aux octets `blob[off[i] .. off[i+1]]`, qu'on
redécoupe sur l'octet séparateur `0x01` pour obtenir voie / code_postal / ville.

---

## 4. Comment ça marche ?

### Normalisation (accents + casse)

La **même** fonction `normalize` est appliquée à la construction **et** à la
requête. Elle :

1. met en minuscules ;
2. remplace `'` et `-` par des espaces ;
3. retire les accents (décomposition Unicode **NFD**, puis suppression des
   *combining marks* `U+0300..=U+036F`, donc `é → e`, `ç → c`) ;
4. réduit les espaces multiples et coupe aux bords.

Comme l'index et la requête sont normalisés à l'identique, une requête accentuée
ou en majuscules retrouve naturellement les mots stockés sans accent.

### FST + automate de Levenshtein

Pour chaque mot de la requête, on construit un **automate** qui accepte :

- les variantes avec **fautes de frappe** : un **automate de Levenshtein** de
  distance 1 (mots ≤ 4 lettres) ou 2 (mots plus longs). La distance de
  Levenshtein est le nombre minimal d'insertions/suppressions/substitutions ;
- les **préfixes** : `Str::new(mot).starts_with()`.

On fait l'**union** des deux automates, puis on interroge le FST en **une seule
passe** : il renvoie tous les mots indexés acceptés. Chaque mot trouvé donne sa
liste de rid (via la valeur empaquetée), avec un **poids de similarité** dans
`[0, 1]` (1 = identique, 0,9..1 = préfixe, sinon `1 − distance / longueur`).

### Sémantique ET + score

Un enregistrement n'est conservé que s'il correspond à **tous** les mots de la
requête (intersection des listes). Son **score** est la somme des meilleurs
poids obtenus pour chaque mot. Les résultats sont triés par score décroissant,
puis par rid croissant (ordre déterministe).

### mmap

Les 3 fichiers sont lus en *memory-map* : l'OS projette le fichier en mémoire
virtuelle sans le copier entièrement, et charge les pages à la demande. C'est
rapide à ouvrir et économe en RAM.

---

## 5. Exemple de tailles et de latences (échantillon 50 000 lignes)

| Fichier        | Taille  |
|----------------|---------|
| `index.fst`    | 0,22 Mo |
| `postings.bin` | 1,17 Mo |
| `records.bin`  | 1,95 Mo |

Latences mesurées : ~3 à 7 ms par requête.
