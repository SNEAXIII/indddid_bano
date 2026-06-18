package com.example.bano.pure;

/**
 * Abstraction de la structure de jetons. Sa seule responsabilité : pour un jeton
 * de requête, marquer dans le bitset {@code matched} (indexé par index vocab) tous
 * les jetons retenus = union(préfixe, automate de Levenshtein &le; maxDist).
 *
 * Deux implémentations rendent EXACTEMENT le même ensemble (donc même score, même
 * tri, même résultats) : {@link FlatTrieMatcher} (trie aplati maison) et
 * {@link FstMatcher} (FST Lucene). Le scoring/intersection/tri vit dans
 * {@link PureIndex} et ne dépend pas de l'implémentation -> parité par construction.
 */
public interface TokenMatcher extends AutoCloseable {
    /**
     * Marque les index vocab des jetons à distance d'édition &le; {@code maxDist} de
     * {@code qtok}, OU dont {@code qtok} est un préfixe.
     *
     * @param matched bitset (longs) ; bit i = jeton vocab i retenu. Non remis à zéro ici.
     * @param deadlineNanos échéance {@link System#nanoTime()} ; dépassement -> {@link PureIndex.TimeoutException}.
     */
    void match(String qtok, int maxDist, long[] matched, long deadlineNanos);

    @Override
    default void close() {}
}
