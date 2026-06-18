package com.example.bano.pure;

import static org.junit.Assert.assertEquals;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.TreeSet;
import org.junit.Test;

/**
 * Parité au niveau MATCHER : {@link FlatTrieMatcher} (référence, distance par caractère
 * comme le Rust) ↔ {@link FstMatcher} (FST Lucene ∩ automate de Levenshtein) doivent
 * retenir EXACTEMENT le même ensemble de jetons pour une requête donnée.
 *
 * <p>Le point dur = les jetons <b>non-ASCII</b> (œ, °, ᵉ… que {@code normalize} laisse en
 * UTF-8 multi-octets). La distance doit se compter PAR CARACTÈRE des deux côtés. Une régression
 * où le {@code FstMatcher} compterait en octets (ex. {@code CompiledAutomaton} {@code isBinary=true})
 * ferait diverger ces cas — ce que {@link FstParityTest} (mini-index tout ASCII) ne voit pas.</p>
 */
public class MatcherParityTest {

    /** Jetons normalisés plausibles, dont des non-ASCII (œ, °, exposant ᵉ) + leurs voisins ASCII. */
    private static final String[] RAW_TOKENS = {
            "coeur", "cœur", "soeur", "sœur", "oeuvre", "œuvre",
            "rue", "ruelle", "ruette", "remy",
            "degre", "5", "5e", "5ᵉ", "n", "n°", "122°",
    };

    private static final String[] QUERIES = {
            // non-ASCII : c'est ici que isBinary=true cassait
            "coeur", "cœur", "soeur", "sœur", "oeuvre", "œuvre",
            "5e", "5ᵉ", "n°", "122°", "n",
            // contrôles ASCII
            "rue", "ru", "ruel", "remy", "rem", "xyz", "degre",
    };

    @Test public void memeMatchedTrieEtFst() {
        // Lucene Builder exige des clés strictement croissantes en ordre d'octets UTF-8.
        String[] tokens = sortedByUtf8(RAW_TOKENS);

        try (FlatTrieMatcher trie = new FlatTrieMatcher(tokens);
             FstMatcher fst = new FstMatcher(tokens)) {
            for (String q : QUERIES) {
                int d = q.codePointCount(0, q.length()) <= 4 ? 1 : 2;
                TreeSet<String> aSet = matchedTokens(trie, tokens, q, d);
                TreeSet<String> bSet = matchedTokens(fst, tokens, q, d);
                assertEquals("matched différent pour q=\"" + q + "\" (d=" + d + ")", aSet, bSet);
            }
        }
    }

    /** Lance {@code matcher.match} et renvoie l'ensemble (lisible) des jetons retenus. */
    private static TreeSet<String> matchedTokens(TokenMatcher m, String[] tokens, String q, int d) {
        long[] matched = new long[(tokens.length + 63) >>> 6];
        m.match(q, d, matched, Long.MAX_VALUE);
        TreeSet<String> out = new TreeSet<>();
        for (int wi = 0; wi < matched.length; wi++) {
            long w = matched[wi];
            while (w != 0) {
                int vi = (wi << 6) + Long.numberOfTrailingZeros(w);
                w &= w - 1;
                out.add(tokens[vi]);
            }
        }
        return out;
    }

    /** Trie une copie des jetons par octets UTF-8 (non signés) — ordre du build FST. */
    private static String[] sortedByUtf8(String[] in) {
        List<String> l = new ArrayList<>(Arrays.asList(in));
        l.sort((a, b) -> {
            byte[] ba = a.getBytes(StandardCharsets.UTF_8);
            byte[] bb = b.getBytes(StandardCharsets.UTF_8);
            int n = Math.min(ba.length, bb.length);
            for (int i = 0; i < n; i++) {
                int x = (ba[i] & 0xFF) - (bb[i] & 0xFF);
                if (x != 0) return x;
            }
            return ba.length - bb.length;
        });
        return l.toArray(new String[0]);
    }
}
