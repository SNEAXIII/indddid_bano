# Formats binaires de l'artefact BANO

Tout est **little-endian**. Source de vérité : `demo/rust/bano-fst/src/build.rs`
(écriture) et `src/index.rs` (lecture Rust). Côté Java : `pure/Vocab.java`,
`pure/Postings.java`, `pure/Records.java`.

Un artefact = un dossier contenant 4 fichiers. Le Rust lit `index.fst` ; le Java
lit `vocab.bin`. Les deux décrivent le MÊME dictionnaire trié.

## index.fst

Format du crate `fst` (`fst::Map`). **Opaque hors de Rust.** Associe une clé
(jeton, en octets) à une valeur `u64` `packed`. Construit avec `MapBuilder`, qui
exige une insertion dans l'ordre **croissant des octets** des clés.

Pour l'inspecter sans Rust : passe par `vocab.bin` (mêmes données, voir plus
bas). Pour l'inspecter en Rust, un petit binaire/test qui ouvre `fst::Map` et
stream les paires suffit.

## vocab.bin

Miroir plat et lisible du FST, écrit dans le même `build`. Lu par le moteur Java.

```
u32  n                      nombre de jetons
u32  offsets[n+1]           position de chaque jeton dans le blob (offsets[n] = taille blob)
u64  packed[n]              valeur packed de chaque jeton (même ordre que les jetons)
u8   blob[...]              jetons UTF-8 concaténés, TRIÉS par octets
```

Jeton `i` = `blob[offsets[i] .. offsets[i+1]]`. L'ordre trié permet la recherche
binaire. Le test `vocab_bin_matches_fst` (build.rs) garantit
`fst.get(token) == packed[i]` pour tout i.

### packed (u64)

```
packed = (offset_postings << 32) | len
  offset_postings : position du 1er rid dans postings.bin, EN UNITÉS u32 (pas en octets)
  len             : nombre de rid pour ce jeton (32 bits de poids faible)
```

Décodage : `offset = packed >> 32`, `len = packed & 0xFFFFFFFF`.

## postings.bin

```
u32  rid[...]               tous les rid, jeton après jeton (ordre du vocab trié)
```

Pas d'en-tête. Les rid du jeton `i` sont
`rid[offset_postings .. offset_postings + len]` (indices en u32). En octets :
`offset_postings * 4`. Chaque rid est un numéro de ligne (0-based) du CSV source.

## records.bin

Données d'affichage (avec accents/casse d'origine, NON normalisées).

```
u32  n                      nombre d'enregistrements
u32  offsets[n+1]           position de chaque record dans le blob (offsets[n] = taille blob)
u8   blob[...]              records UTF-8 concaténés
```

Record `rid` = `blob[offsets[rid] .. offsets[rid+1]]`, puis champs séparés par
l'octet `0x01` : `voie \x01 code_postal \x01 ville`. Le `0x01` est choisi parce
qu'il n'apparaît jamais dans une adresse.

## Invariants à vérifier (cmd `check`)

- `vocab.bin` trié par octets (sinon le FST n'aurait pas pu être construit).
- `Σ len(jeton) == nombre de u32 dans postings.bin`.
- tout `rid` de `postings.bin` est `< n` de `records.bin`.
- `fst.get(token) == vocab.packed[token]` (test Rust `vocab_bin_matches_fst`).
