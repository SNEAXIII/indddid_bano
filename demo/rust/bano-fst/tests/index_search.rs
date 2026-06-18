//! Test d'intégration : build d'un mini-index dans un dossier temporaire, puis
//! recherche via `Index`. Vérifie le bout-en-bout build -> open -> search.

use std::fs;

use bano_fst::build::build;
use bano_fst::index::Index;

#[test]
fn build_open_search_trouve_la_cible() {
    // Dossier temporaire unique (PID) sous le répertoire temp du système.
    let base = std::env::temp_dir().join(format!("bano_fst_test_{}", std::process::id()));
    let _ = fs::remove_dir_all(&base);
    fs::create_dir_all(&base).unwrap();

    let csv_path = base.join("streets.csv");
    fs::write(
        &csv_path,
        "voie,code_postal,ville\nRue de la Paix,01000,Bourg-en-Bresse\nAvenue Carnot,75017,Paris\n",
    )
    .unwrap();

    let index_dir = base.join("index");
    build(csv_path.to_str().unwrap(), index_dir.to_str().unwrap()).unwrap();

    let index = Index::open(index_dir.to_str().unwrap()).unwrap();

    // Faute de frappe + multi-mots : doit retrouver Bourg-en-Bresse.
    let hits = index.search("bourg bress", 5).unwrap();
    assert!(
        hits.iter().any(|h| h.ville == "Bourg-en-Bresse"),
        "attendu Bourg-en-Bresse, obtenu : {hits:?}"
    );

    let _ = fs::remove_dir_all(&base);
}
