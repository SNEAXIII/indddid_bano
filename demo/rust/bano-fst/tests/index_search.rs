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

/// Parité séquentiel ↔ parallèle : les deux moteurs (utilisés par la démo de
/// comparaison) doivent renvoyer EXACTEMENT les mêmes résultats. Seule la
/// latence diffère ; le contenu/ordre est identique.
#[test]
fn search_seq_et_parallele_donnent_le_meme_resultat() {
    let base = std::env::temp_dir().join(format!("bano_fst_seqpar_{}", std::process::id()));
    let _ = fs::remove_dir_all(&base);
    fs::create_dir_all(&base).unwrap();

    let csv_path = base.join("streets.csv");
    fs::write(
        &csv_path,
        "voie,code_postal,ville\n\
         Rue de la Paix,01000,Bourg-en-Bresse\n\
         Avenue Carnot,75017,Paris\n\
         Rue de la Republique,69001,Lyon\n\
         Place de la Bourse,33000,Bordeaux\n",
    )
    .unwrap();

    let index_dir = base.join("index");
    build(csv_path.to_str().unwrap(), index_dir.to_str().unwrap()).unwrap();
    let index = Index::open(index_dir.to_str().unwrap()).unwrap();

    for q in ["rue de la paix", "bourg bress", "place bourse", "ru", "lyon republique"] {
        let par = index.search(q, 5).unwrap();
        let seq = index.search_seq(q, 5).unwrap();
        assert_eq!(par, seq, "résultats divergents pour la requête {q:?}");
    }

    let _ = fs::remove_dir_all(&base);
}
