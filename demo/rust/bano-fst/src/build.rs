//! Module BUILD : transforme le CSV BANO en un artefact binaire compact.
//!
//! L'artefact est composé de 3 fichiers (voir le README pour le détail) :
//!   - index.fst    : un dictionnaire trié (FST) jeton -> position des postings
//!   - postings.bin : pour chaque jeton, la liste des identifiants d'enregistrements (rid)
//!   - records.bin  : les données d'affichage (voie/cp/ville d'origine, AVEC accents)
//!
//! Vocabulaire :
//!   - "rid" (record id) : numéro de ligne (0, 1, 2, ...) dans le CSV.
//!   - "jeton" (token)   : un mot normalisé (ex. "bourg", "bresse", "01000").
//!   - "posting list"    : liste des rid qui contiennent un jeton donné
//!                         (exactement comme l'index d'un livre).
//!   - "FST"             : Finite State Transducer. Ici, via `fst::Map`, c'est
//!                         un dictionnaire trié ultra-compact qui associe une
//!                         CLÉ (le jeton, en octets) à une VALEUR u64.

use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;

// `fst::MapBuilder` permet de construire un `fst::Map` en insérant les paires
// (clé, valeur) — À CONDITION de les insérer dans l'ordre croissant des clés.
use fst::MapBuilder;

// On réutilise la tokenisation définie dans normalize.rs (MÊME normalisation
// qu'à la recherche : c'est ce qui rend la recherche insensible aux accents/casse).
use crate::normalize::tokenize;

/// Point d'entrée du sous-commande `build`.
///
/// `csv_path` : chemin du fichier CSV source.
/// `out_dir`  : dossier où écrire les 3 fichiers de l'artefact.
///
/// Le type de retour `Result<(), Box<dyn std::error::Error>>` signifie :
/// "soit ça réussit et on ne renvoie rien d'utile `()`, soit ça échoue avec
/// une erreur d'un type quelconque". L'opérateur `?` propage ces erreurs.
pub fn build(csv_path: &str, out_dir: &str) -> Result<(), Box<dyn std::error::Error>> {
    // On s'assure que le dossier de sortie existe.
    std::fs::create_dir_all(out_dir)?;

    // ------------------------------------------------------------------
    // 1) LECTURE DU CSV
    // ------------------------------------------------------------------
    // On utilise le crate `csv` pour parser le CSV. Il gère les guillemets, les échappements, etc.
    let mut reader = csv::ReaderBuilder::new()
        .has_headers(true) // la 1re ligne ("voie,code_postal,ville") est ignorée
        .from_path(csv_path)?;

    // `records` : pour chaque rid, on garde la chaîne d'affichage d'origine
    // (NON normalisée), au format "voie\x01code_postal\x01ville".
    // L'octet 0x01 sert de séparateur interne (improbable dans une adresse).
    let mut records: Vec<String> = Vec::new();

    // `postings` : table jeton -> liste de rid. On utilise un HashMap (rapide),
    // et on triera les clés au moment d'écrire le FST (obligatoire : insertion
    // triée).
    let mut postings: HashMap<String, Vec<u32>> = HashMap::new();

    // On parcourt chaque ligne du CSV. `rid` est l'indice de la ligne.
    for (rid, result) in reader.records().enumerate() {
        let row = result?; // une `StringRecord` (les champs de la ligne)

        let voie = row.get(0).unwrap_or("");
        let cp = row.get(1).unwrap_or("");
        let ville = row.get(2).unwrap_or("");

        // Donnée d'affichage : on conserve les accents et la casse d'origine.
        records.push(format!("{voie}\x01{cp}\x01{ville}"));

        // Pour l'indexation, on normalise et on tokenise l'ensemble voie+cp+ville.
        // Exemple : "Allée Beaugency 01000 Bourg-en-Bresse"
        //   -> ["allee","beaugency","01000","bourg","en","bresse"]
        let tokens = tokenize(&format!("{voie} {cp} {ville}"));

        // Un même jeton peut apparaître plusieurs fois dans une ligne ; on ne
        // veut ajouter le rid qu'UNE SEULE FOIS à la posting list de ce jeton.
        // Le HashSet sert à supprimer les jetons en doublon de CETTE ligne.
        let mut seen = HashSet::new();
        let rid_u32 = rid as u32;
        for tok in tokens {
            // `seen.insert` renvoie true si le jeton n'était pas déjà vu.
            if seen.insert(tok.clone()) {
                postings.entry(tok).or_default().push(rid_u32);
            }
        }
    }

    let n_records = records.len();
    let n_tokens = postings.len();

    // ------------------------------------------------------------------
    // 2) ÉCRITURE DE records.bin
    // ------------------------------------------------------------------
    // Format :
    //   u32 n                      (nombre d'enregistrements)
    //   (n+1) u32 offsets          (positions dans le blob ; le dernier = taille du blob)
    //   blob : les octets UTF-8 de chaque enregistrement, concaténés.
    // Pour relire l'enregistrement i : blob[off[i] .. off[i+1]].
    {
        let f = File::create(Path::new(out_dir).join("records.bin"))?;
        let mut w = BufWriter::new(f); // BufWriter = écriture tamponnée = bien plus rapide

        // En-tête : nombre d'enregistrements (little-endian = octet de poids faible d'abord).
        w.write_all(&(n_records as u32).to_le_bytes())?;

        // Table des offsets. On calcule la position cumulée de chaque blob.
        // Il y a n+1 offsets : off[0]=0, ..., off[n]=taille totale du blob.
        let mut offset: u32 = 0;
        for rec in &records {
            w.write_all(&offset.to_le_bytes())?;
            offset += rec.len() as u32; // len() = nombre d'octets UTF-8
        }
        // Offset final (sentinelle) = taille totale du blob.
        w.write_all(&offset.to_le_bytes())?;

        // Le blob lui-même : tous les enregistrements bout à bout.
        for rec in &records {
            w.write_all(rec.as_bytes())?;
        }
        w.flush()?; // on vide le tampon sur le disque
    }

    // ------------------------------------------------------------------
    // 3) ÉCRITURE de postings.bin + CONSTRUCTION de index.fst (ensemble)
    // ------------------------------------------------------------------
    // Le FST exige une insertion des clés dans l'ordre croissant des OCTETS.
    // On trie donc les jetons. (Pour de l'ASCII/normalisé, l'ordre des octets
    // correspond à l'ordre alphabétique attendu.)
    let mut tokens_sorted: Vec<&String> = postings.keys().collect();
    tokens_sorted.sort();

    // Fichier postings.bin : on y écrit, jeton après jeton (dans l'ordre trié),
    // les rid en u32 little-endian.
    let postings_file = File::create(Path::new(out_dir).join("postings.bin"))?;
    let mut postings_writer = BufWriter::new(postings_file);

    // Constructeur du FST, qui écrit directement dans index.fst (tamponné).
    let fst_file = File::create(Path::new(out_dir).join("index.fst"))?;
    let fst_writer = BufWriter::new(fst_file);
    let mut map_builder = MapBuilder::new(fst_writer)?;

    // `cursor` = position courante dans postings.bin, comptée EN U32 (pas en octets).
    let mut cursor: u64 = 0;

    // Accumulateurs pour vocab.bin (index plat lisible par Java).
    let n_vocab = tokens_sorted.len();
    let mut vocab_offsets: Vec<u32> = Vec::with_capacity(n_vocab + 1);
    let mut vocab_packed: Vec<u64> = Vec::with_capacity(n_vocab);
    let mut vocab_blob: Vec<u8> = Vec::new();

    for tok in tokens_sorted {
        let rids = &postings[tok];
        let len = rids.len() as u64;

        let packed: u64 = (cursor << 32) | len;
        map_builder.insert(tok.as_bytes(), packed)?;

        for &rid in rids {
            postings_writer.write_all(&rid.to_le_bytes())?;
        }
        cursor += len;

        // Même jeton, même tri, même packed que le FST -> données identiques.
        vocab_offsets.push(vocab_blob.len() as u32);
        vocab_packed.push(packed);
        vocab_blob.extend_from_slice(tok.as_bytes());
    }
    vocab_offsets.push(vocab_blob.len() as u32); // sentinelle = taille du blob

    map_builder.finish()?;
    postings_writer.flush()?;

    // vocab.bin : u32 n | (n+1) u32 offsets | n u64 packed | blob jetons UTF-8 trié.
    {
        let f = File::create(Path::new(out_dir).join("vocab.bin"))?;
        let mut w = BufWriter::new(f);
        w.write_all(&(n_vocab as u32).to_le_bytes())?;
        for off in &vocab_offsets {
            w.write_all(&off.to_le_bytes())?;
        }
        for p in &vocab_packed {
            w.write_all(&p.to_le_bytes())?;
        }
        w.write_all(&vocab_blob)?;
        w.flush()?;
    }

    // ------------------------------------------------------------------
    // 4) RÉSUMÉ AFFICHÉ
    // ------------------------------------------------------------------
    let mb = |p: &str| -> f64 {
        std::fs::metadata(Path::new(out_dir).join(p))
            .map(|m| m.len() as f64 / (1024.0 * 1024.0))
            .unwrap_or(0.0)
    };
    println!("Construction terminee.");
    println!("  Enregistrements : {n_records}");
    println!("  Jetons uniques  : {n_tokens}");
    println!("  index.fst    : {:.2} Mo", mb("index.fst"));
    println!("  postings.bin : {:.2} Mo", mb("postings.bin"));
    println!("  records.bin  : {:.2} Mo", mb("records.bin"));
    println!("  vocab.bin    : {:.2} Mo", mb("vocab.bin"));

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Read;

    #[test]
    fn vocab_bin_matches_fst() {
        let dir = std::env::temp_dir().join("bano_vocab_test");
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).unwrap();
        let csv = dir.join("streets.csv");
        std::fs::write(
            &csv,
            "voie,code_postal,ville\nRue de la Paix,75002,Paris\nRue du Bourg,01000,Bourg\n",
        )
        .unwrap();

        build(csv.to_str().unwrap(), dir.to_str().unwrap()).unwrap();

        let mut bytes = Vec::new();
        File::open(dir.join("vocab.bin"))
            .unwrap()
            .read_to_end(&mut bytes)
            .unwrap();

        let n = u32::from_le_bytes(bytes[0..4].try_into().unwrap()) as usize;
        let off_start = 4;
        let packed_start = off_start + (n + 1) * 4;
        let blob_start = packed_start + n * 8;

        let map = fst::Map::new(std::fs::read(dir.join("index.fst")).unwrap()).unwrap();
        assert_eq!(map.len(), n, "vocab et fst doivent avoir le meme nombre de jetons");

        for i in 0..n {
            let o = u32::from_le_bytes(
                bytes[off_start + i * 4..off_start + i * 4 + 4].try_into().unwrap(),
            ) as usize;
            let o2 = u32::from_le_bytes(
                bytes[off_start + (i + 1) * 4..off_start + (i + 1) * 4 + 4].try_into().unwrap(),
            ) as usize;
            let tok = std::str::from_utf8(&bytes[blob_start + o..blob_start + o2]).unwrap();
            let packed = u64::from_le_bytes(
                bytes[packed_start + i * 8..packed_start + i * 8 + 8].try_into().unwrap(),
            );
            assert_eq!(map.get(tok.as_bytes()), Some(packed), "packed du jeton {tok}");
        }
    }
}
