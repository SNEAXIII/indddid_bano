package com.example.bano.pure;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class LevenshteinTest {
    @Test public void distanceConnue() {
        assertEquals(3, Levenshtein.distance("kitten", "sitting"));
        assertEquals(0, Levenshtein.distance("paris", "paris"));
        assertEquals(1, Levenshtein.distance("abc", "abd"));
    }
    @Test public void similariteExacte() {
        assertEquals(1.0f, Levenshtein.similarity("paris", "paris"), 1e-6f);
    }
    @Test public void similaritePrefixe() {
        // 0.9 + 0.1 * (2/3)
        assertEquals(0.9f + 0.1f * (2f / 3f), Levenshtein.similarity("ab", "abc"), 1e-6f);
    }
    @Test public void similariteFuzzy() {
        // 1 - 1/3
        assertEquals(1.0f - 1f / 3f, Levenshtein.similarity("abc", "abd"), 1e-6f);
    }
}
