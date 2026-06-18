package com.example.bano.bench;

import com.example.bano.Result;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public final class BenchMetrics {
    private BenchMetrics() {}

    public static double percentile(List<Double> values, double p) {
        if (values.isEmpty()) return 0.0;
        List<Double> o = new ArrayList<>(values);
        Collections.sort(o);
        if (p <= 0) return o.get(0);
        if (p >= 100) return o.get(o.size() - 1);
        double rank = (p / 100.0) * (o.size() - 1);
        int lo = (int) rank;
        int hi = Math.min(lo + 1, o.size() - 1);
        double frac = rank - lo;
        return o.get(lo) + (o.get(hi) - o.get(lo)) * frac;
    }

    public static boolean matches(Result r, String voie, String cp, String ville) {
        return r.voie().equals(voie) && r.cp().equals(cp) && r.ville().equals(ville);
    }

    public static double recallAtK(List<Result> results, String voie, String cp, String ville, int k) {
        int lim = Math.min(k, results.size());
        for (int i = 0; i < lim; i++) {
            if (matches(results.get(i), voie, cp, ville)) return 1.0;
        }
        return 0.0;
    }

    public static double reciprocalRank(List<Result> results, String voie, String cp, String ville) {
        for (int i = 0; i < results.size(); i++) {
            if (matches(results.get(i), voie, cp, ville)) return 1.0 / (i + 1);
        }
        return 0.0;
    }

    /** Nombre de mots d'une requête (séparés par des espaces), 0 si vide. */
    public static int wordCount(String query) {
        if (query == null) return 0;
        String trimmed = query.trim();
        if (trimmed.isEmpty()) return 0;
        return trimmed.split("\\s+").length;
    }
}
