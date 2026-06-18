package com.example.bano.pure;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Port EXACT de normalize.rs : minuscules (locale-indépendant), ' et - -> espace,
 * suppression des accents (NFD + retrait des U+0300..U+036F), espaces réduits.
 */
public final class Normalize {
    private Normalize() {}

    public static String normalize(String s) {
        // 1) minuscules — Locale.ROOT pour matcher le to_lowercase() Unicode de Rust.
        String lowered = s.toLowerCase(Locale.ROOT);

        // 2) ' et - deviennent des espaces.
        StringBuilder replaced = new StringBuilder(lowered.length());
        lowered.codePoints().forEach(cp -> {
            if (cp == '\'' || cp == '\"' || cp == '-') replaced.append(' ');
            else replaced.appendCodePoint(cp);
        });

        // 3) NFD puis retrait des marques diacritiques combinantes.
        String decomposed = Normalizer.normalize(replaced.toString(), Normalizer.Form.NFD);
        StringBuilder out = new StringBuilder(decomposed.length());
        decomposed.codePoints().forEach(cp -> {
            if (cp < 0x0300 || cp > 0x036F) out.appendCodePoint(cp);
        });

        // 4) espaces propres : collapse + trim.
        String[] parts = out.toString().trim().split("\\s+");
        StringBuilder joined = new StringBuilder();
        for (String p : parts) {
            if (p.isEmpty()) continue;
            if (joined.length() > 0) joined.append(' ');
            joined.append(p);
        }
        return joined.toString();
    }

    public static List<String> tokenize(String s) {
        String n = normalize(s);
        List<String> out = new ArrayList<>();
        if (n.isEmpty()) return out;
        for (String t : n.split(" ")) {
            if (!t.isEmpty()) out.add(t);
        }
        return out;
    }
}
