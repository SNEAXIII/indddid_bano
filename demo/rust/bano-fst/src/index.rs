//! Module INDEX : ouverture des 3 fichiers en mmap + recherche floue.
//!
//! La recherche est identique à l'ancienne sous-commande `search`, mais elle
//! RENVOIE une liste de résultats (`Hit`) au lieu de les imprimer. Cela permet
//! de la réutiliser depuis la CLI (qui imprime) ET depuis le pont JNI (qui
//! sérialise en JSON).

use std::collections::HashMap;
use std::error::Error;
use std::fs::File;
use std::path::Path;

use fst::automaton::{Automaton, Levenshtein, Str};
use fst::{IntoStreamer, Map, Streamer};
use memmap2::Mmap;
use rayon::prelude::*;

use crate::normalize::tokenize;

/// Active les traces `[DEBUG]` seulement si la variable d'env `BANO_DEBUG` est
/// definie (n'importe quelle valeur). Lu une seule fois puis mis en cache.
fn debug_enabled() -> bool {
    use std::sync::OnceLock;
    static DEBUG: OnceLock<bool> = OnceLock::new();
    *DEBUG.get_or_init(|| std::env::var_os("BANO_DEBUG").is_some())
}

/// `eprintln!` conditionnel : n'imprime que si `BANO_DEBUG` est definie.
macro_rules! dbgln {
    ($($arg:tt)*) => {
        if $crate::index::debug_enabled() {
            eprintln!($($arg)*);
        }
    };
}

/// Un résultat de recherche : score + triplet d'adresse (avec accents d'origine).
#[derive(Debug, Clone, PartialEq)]
pub struct Hit {
    pub score: f32,
    pub voie: String,
    pub cp: String,
    pub ville: String,
}

/// Index ouvert : les 3 fichiers projetés en mémoire (mmap). On garde les
/// `Mmap` en vie ; la `fst::Map` est reconstruite à chaque recherche (coût
/// négligeable : simple validation d'en-tête) pour éviter une structure
/// auto-référente (Map emprunterait `fst_mmap`).
pub struct Index {
    fst_mmap: Mmap,
    postings_mmap: Mmap,
    records_mmap: Mmap,
}

impl Index {
    /// Ouvre l'artefact (dossier contenant index.fst / postings.bin / records.bin).
    pub fn open(dir: &str) -> Result<Index, Box<dyn Error>> {
        let dir = Path::new(dir);
        Ok(Index {
            fst_mmap: map_file(dir.join("index.fst"))?,
            postings_mmap: map_file(dir.join("postings.bin"))?,
            records_mmap: map_file(dir.join("records.bin"))?,
        })
    }

    /// Recherche floue + préfixe, sémantique ET, renvoie les `limit` meilleurs.
    /// Variante **parallèle** : les parcours FST par jeton tournent sur rayon.
    pub fn search(&self, query: &str, limit: usize) -> Result<Vec<Hit>, Box<dyn Error>> {
        self.search_impl(query, limit, true)
    }

    pub fn search_seq(&self, query: &str, limit: usize) -> Result<Vec<Hit>, Box<dyn Error>> {
        self.search_impl(query, limit, false)
    }

    fn search_impl(
        &self,
        query: &str,
        limit: usize,
        parallel: bool,
    ) -> Result<Vec<Hit>, Box<dyn Error>> {
        let map = Map::new(&self.fst_mmap)?;
        let postings: &[u8] = &self.postings_mmap;
        let records: &[u8] = &self.records_mmap;

        let qtokens = tokenize(query);
        dbgln!("[DEBUG] query={:?} -> tokens={:?} parallel={}", query, qtokens, parallel); // DEBUG
        if qtokens.is_empty() {
            dbgln!("[DEBUG] aucun token -> 0 resultat"); // DEBUG
            return Ok(Vec::new());
        }

        let one = |qtok: &String| -> HashMap<u32, f32> {
            let d = if qtok.chars().count() <= 4 { 1 } else { 2 };
            dbgln!("[DEBUG] token={:?} distance_levenshtein_max={}", qtok, d); // DEBUG
            let scores = match Levenshtein::new(qtok, d) {
                Ok(lev) => {
                    let pref = Str::new(qtok).starts_with();
                    let aut = lev.union(pref);
                    collect(&map, aut, qtok, postings)
                }
                Err(_) => {
                    let aut = Str::new(qtok).starts_with();
                    collect(&map, aut, qtok, postings)
                }
            };
            dbgln!("[DEBUG]   token={:?} -> {} records distincts touches", qtok, scores.len()); // DEBUG
            scores
        };

        let per_token_maps: Vec<HashMap<u32, f32>> = if parallel {
            qtokens.par_iter().map(&one).collect()
        } else {
            qtokens.iter().map(&one).collect()
        };

        // Intersection (ET) en additionnant les poids.
        let mut acc: HashMap<u32, f32> = per_token_maps[0].clone();
        for next in &per_token_maps[1..] {
            let mut merged: HashMap<u32, f32> = HashMap::new();
            for (rid, w) in &acc {
                if let Some(w2) = next.get(rid) {
                    merged.insert(*rid, w + w2);
                }
            }
            acc = merged;
        }
        dbgln!("[DEBUG] intersection ET -> {} records survivent", acc.len()); // DEBUG

        let mut candidates: Vec<(u32, f32)> = acc.into_iter().collect();
        candidates.sort_by(|a, b| {
            b.1.partial_cmp(&a.1)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then(a.0.cmp(&b.0))
        });
        candidates.truncate(limit);
        dbgln!("[DEBUG] top {} apres tri/troncature: {:?}", limit, candidates); // DEBUG

        // Décodage records.bin : [u32 n][ (n+1) u32 offsets ][ blob ].
        let n = read_u32(records, 0) as usize;
        let offsets_start = 4;
        let blob_start = offsets_start + (n + 1) * 4;

        let mut hits = Vec::with_capacity(candidates.len());
        for (rid, score) in &candidates {
            let i = *rid as usize;
            let off = read_u32(records, offsets_start + i * 4) as usize;
            let off_next = read_u32(records, offsets_start + (i + 1) * 4) as usize;
            let bytes = &records[blob_start + off..blob_start + off_next];
            let text = std::str::from_utf8(bytes)?;
            let mut parts = text.split('\u{0001}');
            hits.push(Hit {
                score: *score,
                voie: parts.next().unwrap_or("").to_string(),
                cp: parts.next().unwrap_or("").to_string(),
                ville: parts.next().unwrap_or("").to_string(),
            });
        }
        dbgln!("[DEBUG] {} hits decodes:", hits.len()); // DEBUG
        for h in &hits {
            dbgln!("[DEBUG]   {:.3}  {} {} {}", h.score, h.voie, h.cp, h.ville); // DEBUG
        }
        Ok(hits)
    }
}

/// Sérialise des `Hit` en JSON (sans dépendance externe). On échappe les
/// guillemets et antislashs présents dans les champs texte.
pub fn hits_to_json(hits: &[Hit]) -> String {
    fn esc(s: &str) -> String {
        let mut out = String::with_capacity(s.len() + 2);
        for c in s.chars() {
            match c {
                '"' => out.push_str("\\\""),
                '\\' => out.push_str("\\\\"),
                '\n' => out.push_str("\\n"),
                '\r' => out.push_str("\\r"),
                '\t' => out.push_str("\\t"),
                _ => out.push(c),
            }
        }
        out
    }
    let mut out = String::from("[");
    for (i, h) in hits.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        out.push_str(&format!(
            "{{\"score\":{:.3},\"voie\":\"{}\",\"cp\":\"{}\",\"ville\":\"{}\"}}",
            h.score,
            esc(&h.voie),
            esc(&h.cp),
            esc(&h.ville)
        ));
    }
    out.push(']');
    out
}

fn map_file(path: std::path::PathBuf) -> Result<Mmap, Box<dyn Error>> {
    let f = File::open(path)?;
    let m = unsafe { Mmap::map(&f)? };
    Ok(m)
}

fn read_u32(bytes: &[u8], at: usize) -> u32 {
    u32::from_le_bytes([bytes[at], bytes[at + 1], bytes[at + 2], bytes[at + 3]])
}

fn levenshtein(a: &str, b: &str) -> usize {
    let a: Vec<char> = a.chars().collect();
    let b: Vec<char> = b.chars().collect();
    let mut prev: Vec<usize> = (0..=b.len()).collect();
    let mut curr: Vec<usize> = vec![0; b.len() + 1];
    for i in 1..=a.len() {
        curr[0] = i;
        for j in 1..=b.len() {
            let cost = if a[i - 1] == b[j - 1] { 0 } else { 1 };
            curr[j] = (prev[j] + 1).min(curr[j - 1] + 1).min(prev[j - 1] + cost);
        }
        std::mem::swap(&mut prev, &mut curr);
    }
    prev[b.len()]
}

fn similarity(qtok: &str, matched: &str) -> f32 {
    if qtok == matched {
        return 1.0;
    }
    if matched.starts_with(qtok) {
        let ratio = qtok.chars().count() as f32 / matched.chars().count().max(1) as f32;
        return 0.9 + 0.1 * ratio;
    }
    let d = levenshtein(qtok, matched) as f32;
    let max_len = qtok.chars().count().max(matched.chars().count()).max(1) as f32;
    (1.0 - d / max_len).max(0.0)
}

fn collect<A: Automaton>(
    map: &Map<&Mmap>,
    aut: A,
    qtok: &str,
    postings: &[u8],
) -> HashMap<u32, f32> {
    let mut scores: HashMap<u32, f32> = HashMap::new();
    let mut stream = map.search(&aut).into_stream();
    while let Some((kbytes, packed)) = stream.next() {
        let matched = match std::str::from_utf8(kbytes) {
            Ok(s) => s,
            Err(_) => continue,
        };
        let offset = (packed >> 32) as usize;
        let len = (packed & 0xFFFF_FFFF) as usize;
        let w = similarity(qtok, matched);
        dbgln!("[DEBUG]     fst match {:?}~{:?} poids={:.3} postings={}", qtok, matched, w, len); // DEBUG
        for k in 0..len {
            let rid = read_u32(postings, (offset + k) * 4);
            let entry = scores.entry(rid).or_insert(0.0);
            if w > *entry {
                *entry = w;
            }
        }
    }
    return scores;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_escape_et_format() {
        let hits = vec![Hit {
            score: 2.0,
            voie: "Rue de l'\"Eglise\"".to_string(),
            cp: "01000".to_string(),
            ville: "Bourg-en-Bresse".to_string(),
        }];
        let json = hits_to_json(&hits);
        assert_eq!(
            json,
            "[{\"score\":2.000,\"voie\":\"Rue de l'\\\"Eglise\\\"\",\"cp\":\"01000\",\"ville\":\"Bourg-en-Bresse\"}]"
        );
    }

    #[test]
    fn json_vide() {
        assert_eq!(hits_to_json(&[]), "[]");
    }
}
