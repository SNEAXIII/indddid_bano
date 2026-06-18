//! Module de NORMALISATION du texte.
//!
//! Pourquoi normaliser ? 
//! Pour rendre la recherche insensible aux accents ET à la casse
//! Par exemple "BESANCON", "Besançon" et "besancon" sont tous normalisés en "besancon".

// On importe le trait qui fournit la méthode `.nfd()` (décomposition Unicode).
use unicode_normalization::UnicodeNormalization;

/// Normalise une chaîne : minuscules, sans accents, espaces propres.
/// 
/// 1. tout en minuscules ;
/// 2. les apostrophes `'` puis `"` et les tirets `-` deviennent des espaces ;
/// 3. on retire les accents
/// 4. on supprime les espaces multiples et ceux aux bords.
pub fn normalize(s: &str) -> String {
    // --- Étape 1 : minuscules ---
    let lowered = s.to_lowercase();

    // --- Étape 2 : remplacer ', " et - par des espaces ---
    let replaced: String = lowered
        .chars()
        .map(|c| if matches!(c, '\'' | '"' | '-') { ' ' } else { c })
        .collect();

    // --- Étape 3 : retirer les accents ---
    // `.nfd()` décompose chaque caractère accentué en (lettre de base + accent).
    //   Exemple : 'é' -> 'e' + U+0301 (accent aigu "combinant").
    // On supprime alors les caractères de la plage U+0300..=U+036F (la zone Unicode des "Combining Diacritical Marks")
    // Résultat : 'é' -> 'e', 'ç' -> 'c', etc.
    let without_accents: String = replaced
        .nfd()
        .filter(|c| !('\u{0300}'..='\u{036F}').contains(c))
        .collect();

    // --- Étape 4 : espaces propres ---
    // `split_whitespace()` découpe la chaine en mot et les ajoute dans un vecteur puis `join(" ")` les recolle avec un seul espace entre eux.
    without_accents
        .split_whitespace()
        .collect::<Vec<&str>>()
        .join(" ")
}

/// Découpe une chaîne en jetons (mots) normalisés.
pub fn tokenize(s: &str) -> Vec<String> {
    normalize(s)
        .split_whitespace()
        .map(|tok| tok.to_string())
        .collect()
}

// --- Tests unitaires ---
// `#[cfg(test)]` : ce bloc n'est compilé QUE lorsqu'on lance `cargo test`.
// Il ne pèse rien dans le binaire final.
#[cfg(test)]
mod tests {
    use super::*; // importe normalize() et tokenize() du module parent

    #[test]
    fn apostrophe_et_accent() {
        assert_eq!(normalize("Rue de l'Égalité"), "rue de l egalite");
    }

    #[test]
    fn tiret_et_accent() {
        assert_eq!(normalize("Saint-Étienne"), "saint etienne");
    }

    #[test]
    fn majuscules() {
        assert_eq!(normalize("PARIS"), "paris");
    }

    #[test]
    fn guillemets_simples() {
        assert_eq!(normalize("Rue de l\"Eglise\""), "rue de l eglise");
    }

    #[test]
    fn guillemets_doubles() {
        assert_eq!(normalize("Place \"Égalité\""), "place egalite");
    }

    #[test]
    fn espaces_multiples() {
        assert_eq!(normalize("  Bourg   en  Bresse  "), "bourg en bresse");
    }

    #[test]
    fn tokenisation() {
        // "Bourg-en-Bresse" -> 3 jetons après remplacement des tirets.
        assert_eq!(
            tokenize("Bourg-en-Bresse"),
            vec!["bourg".to_string(), "en".to_string(), "bresse".to_string()]
        );
    }
}
