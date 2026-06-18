//! bano-fst : recherche d'adresses floue (fuzzy) HORS LIGNE sur des données BANO.
//!
//! Deux sous-commandes :
//!   - `build <streets.csv> <out_dir>`         : construit l'artefact binaire.
//!   - `search <artifact_dir> "<requete>" [n]` : interroge l'artefact (n = limite).
//!
//! Le programme n'utilise PAS clap : on lit directement les arguments avec
//! `std::env::args()` pour garder les dépendances minimales.

// La logique partagée (build, normalize, index) vit désormais dans la lib
// `bano_fst` (src/lib.rs), réutilisée par le binaire CLI ET par la lib native
// JNI. Le binaire ne garde que le module `search` (impression CLI).
use bano_fst::build;
mod search;

use std::process::exit;

/// Affiche le mode d'emploi puis quitte avec un code d'erreur.
fn usage() -> ! {
    eprintln!("Usage :");
    eprintln!("  bano-fst build  <streets.csv> <out_dir>");
    eprintln!("  bano-fst search <artifact_dir> \"<requete>\" [limit]");
    eprintln!();
    eprintln!("Exemples :");
    eprintln!("  bano-fst build streets.csv ./index");
    eprintln!("  bano-fst search ./index \"bourg en bresse\" 5");
    exit(2); // code 2 = mauvais usage (convention courante)
}

fn main() {
    // `args` contient : [nom_du_programme, arg1, arg2, ...].
    let args: Vec<String> = std::env::args().collect();

    // Il faut au moins une sous-commande (args[1]).
    if args.len() < 2 {
        usage();
    }

    // On aiguille selon la sous-commande. `as_str()` permet de comparer à une
    // chaîne littérale dans le `match`.
    let result: Result<(), Box<dyn std::error::Error>> = match args[1].as_str() {
        "build" => {
            // build <streets.csv> <out_dir>  -> on attend exactement 2 arguments.
            if args.len() != 4 {
                usage();
            }
            build::build(&args[2], &args[3])
        }
        "search" => {
            // search <artifact_dir> "<requete>" [limit]
            if args.len() < 4 || args.len() > 5 {
                usage();
            }
            // Limite optionnelle (5e argument), 10 par défaut.
            let limit = if args.len() == 5 {
                args[4].parse::<usize>().unwrap_or(10)
            } else {
                10
            };
            search::search(&args[2], &args[3], limit)
        }
        // Sous-commande inconnue.
        _ => usage(),
    };

    // Si une erreur a remonté, on l'affiche et on quitte avec un code != 0.
    if let Err(e) = result {
        eprintln!("Erreur : {e}");
        exit(1);
    }
}
