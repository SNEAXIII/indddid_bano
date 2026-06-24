//! bano-fst : recherche d'adresses floue (fuzzy) HORS LIGNE sur des données BANO.
//!
//! Deux sous-commandes :
//!   - `build <streets.csv> <out_dir>`         : construit l'artefact binaire.
//!   - `search <artifact_dir> "<requete>" [n]` : interroge l'artefact (n = limite).

// La logique partagée (build, normalize, index) vit désormais dans la lib
// `bano_fst` (src/lib.rs), réutilisée par le binaire CLI ET par la lib native
// JNI. Le binaire ne garde que le module `search` (impression CLI).
mod search;

use std::{path::PathBuf, process::exit};

use bano_fst::build;
use clap::Parser;

/// Recherche d’adresses floue (fuzzy) HORS LIGNE sur des données BANO
///
/// Exemple :
///     bano-fst build streets.csv index/
///     bano-fst search index/ "bourg en bresse" 5
#[derive(Parser)]
enum Args {
    /// Compile les blobs binaires à partir de la base d’adresses
    Build {
        /// Base d’adresses au format CVS
        cvs_path: PathBuf,

        /// Répertoire de sortie
        out_dir: PathBuf,
    },

    /// Lance une recherche
    Search {
        /// Répertoire des artéfacts
        artifact_dir: PathBuf,

        /// Requête
        request: String,

        /// Limite de résultats
        #[arg(default_value_t = 10)]
        limit: usize,
    },
}

fn main() {
    // Parse la ligne de commande.
    let args = Args::parse();

    // On aiguille selon la sous-commande.
    let result = match args {
        Args::Build { cvs_path, out_dir } => build::build(&cvs_path, &out_dir),
        Args::Search {
            artifact_dir,
            request,
            limit,
        } => search::search(&artifact_dir, &request, limit),
    };

    // Si une erreur a remonté, on l'affiche et on quitte avec un code != 0.
    if let Err(e) = result {
        eprintln!("Erreur : {e}");
        exit(1);
    }
}
