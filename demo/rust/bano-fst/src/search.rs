//! Sous-commande CLI `search` : ouvre l'index, exécute la recherche via
//! `Index::search`, et IMPRIME les résultats + la latence. Toute la logique de
//! recherche vit désormais dans la lib `bano_fst::index`.

use std::error::Error;
use std::time::Instant;

use bano_fst::index::Index;

pub fn search(artifact_dir: &str, query: &str, limit: usize) -> Result<(), Box<dyn Error>> {
    let index = Index::open(artifact_dir)?;

    let start = Instant::now();
    let hits = index.search(query, limit)?;
    let elapsed = start.elapsed();

    if hits.is_empty() {
        println!("Aucun resultat.");
    }
    for h in &hits {
        println!("{:.3}  {} | {} | {}", h.score, h.voie, h.cp, h.ville);
    }
    println!(
        "({} resultat(s), {:.2} ms)",
        hits.len(),
        elapsed.as_secs_f64() * 1000.0
    );
    Ok(())
}
