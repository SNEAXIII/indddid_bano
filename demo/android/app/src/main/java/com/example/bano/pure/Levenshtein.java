package com.example.bano.pure;

/**
 * Port EXACT de index.rs:166-193. Travaille sur les CODE POINTS (scalaires
 * Unicode, comme Rust .chars()), pas sur les char UTF-16. Arithmétique en float
 * pour matcher les f32 de Rust (parité des scores -> recall identique).
 */
public final class Levenshtein {
    private Levenshtein() {}

    public static int distance(String a, String b) {
        int[] ca = a.codePoints().toArray();
        int[] cb = b.codePoints().toArray();
        int[] prev = new int[cb.length + 1];
        int[] curr = new int[cb.length + 1];
        for (int j = 0; j <= cb.length; j++) prev[j] = j;
        for (int i = 1; i <= ca.length; i++) {
            curr[0] = i;
            for (int j = 1; j <= cb.length; j++) {
                int cost = ca[i - 1] == cb[j - 1] ? 0 : 1;
                curr[j] = Math.min(Math.min(prev[j] + 1, curr[j - 1] + 1), prev[j - 1] + cost);
            }
            int[] tmp = prev; prev = curr; curr = tmp;
        }
        return prev[cb.length];
    }

    public static float similarity(String qtok, String matched) {
        if (qtok.equals(matched)) {
            return 1.0f;
        }
        if (matched.startsWith(qtok)) {
            float qlen = qtok.codePointCount(0, qtok.length());
            float mlen = Math.max(1, matched.codePointCount(0, matched.length()));
            return 0.9f + 0.1f * (qlen / mlen);
        }
        float d = distance(qtok, matched);
        float maxLen = Math.max(1, Math.max(
                qtok.codePointCount(0, qtok.length()),
                matched.codePointCount(0, matched.length())));
        return Math.max(0.0f, 1.0f - d / maxLen);
    }
}
