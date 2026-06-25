package com.example.bano;

import android.content.res.AssetManager;

import org.json.JSONArray;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Benchmark on-device des DEUX moteurs Rust : recherche parallèle (rayon) vs
 * séquentielle. Rejoue le même jeu de requêtes (assets/bench/queries.json),
 * entrelacé, avec warmup. Mesure la latence (p50/p95/p99 + moyenne) de chaque
 * moteur et vérifie que les résultats sont identiques (parité = sanity check).
 */
public final class CompareBench {

    /** Stats de latence (ms) d'un moteur. */
    public static final class Stat {
        public double p50, p95, p99, mean;
        public int n;
    }

    /** Latence p50/p99 des deux moteurs pour les requêtes de {@code words} mots. */
    public static final class WcStat {
        public int words;
        public int n;
        public double parP50, parP99, seqP50, seqP99;
    }

    /** Résultat global : latences des deux moteurs + nb d'écarts de parité. */
    public static final class Outcome {
        public Stat parallel = new Stat();
        public Stat seq = new Stat();
        public int mismatches;   // requêtes où seq != parallèle (attendu : 0)
        public int nQueries;
        /** Latence par nombre de mots de la requête, trié croissant. */
        public List<WcStat> byWordCount = new ArrayList<>();
    }

    /** Rappel de progression : {@code done}/{@code total}, {@code phase} = libellé. */
    public interface Progress {
        void onProgress(int done, int total, String phase);
    }

    private final String indexDir;
    private final AssetManager assets;

    public CompareBench(String indexDir, AssetManager assets) {
        this.indexDir = indexDir;
        this.assets = assets;
    }

    private List<String> loadQueries() throws Exception {
        try (InputStream in = assets.open("bench/queries.json")) {
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] b = new byte[1 << 16];
            int n;
            while ((n = in.read(b)) > 0) bos.write(b, 0, n);
            JSONArray arr = new JSONArray(new String(bos.toByteArray(), StandardCharsets.UTF_8));
            List<String> out = new ArrayList<>(arr.length());
            for (int i = 0; i < arr.length(); i++) {
                out.add(arr.getJSONObject(i).getString("query"));
            }
            return out;
        }
    }

    public Outcome run(int limit, int warmup, Progress progress) throws Exception {
        List<String> queries = loadQueries();
        int w0 = Math.min(warmup, queries.size());
        int total = w0 + queries.size();

        BanoFst rust = new BanoFst(indexDir);
        try {
            // Warmup : on chauffe les DEUX moteurs (JIT, pool rayon, caches).
            for (int i = 0; i < w0; i++) {
                String q = queries.get(i);
                rust.search(q, limit);
                rust.searchSeq(q, limit);
                tick(progress, i + 1, total, "warmup");
            }

            List<Double> par = new ArrayList<>(queries.size());
            List<Double> seq = new ArrayList<>(queries.size());
            // Latences ventilées par nombre de mots de la requête (clé triée).
            Map<Integer, List<Double>> parByWc = new TreeMap<>();
            Map<Integer, List<Double>> seqByWc = new TreeMap<>();
            int mismatches = 0, done = 0;

            for (String q : queries) {
                long a = System.nanoTime();
                List<Result> ph = rust.search(q, limit);
                double pms = (System.nanoTime() - a) / 1e6;

                long b = System.nanoTime();
                List<Result> sh = rust.searchSeq(q, limit);
                double sms = (System.nanoTime() - b) / 1e6;

                par.add(pms);
                seq.add(sms);
                int wc = wordCount(q);
                bucket(parByWc, wc).add(pms);
                bucket(seqByWc, wc).add(sms);
                if (!sameResults(ph, sh)) mismatches++;

                tick(progress, w0 + (++done), total, "mesure");
            }

            Outcome o = new Outcome();
            o.parallel = stat(par);
            o.seq = stat(seq);
            o.mismatches = mismatches;
            o.nQueries = queries.size();
            o.byWordCount = wordCountStats(parByWc, seqByWc);
            return o;
        } finally {
            rust.close();
        }
    }

    private static boolean sameResults(List<Result> a, List<Result> b) {
        if (a.size() != b.size()) return false;
        for (int i = 0; i < a.size(); i++) {
            Result x = a.get(i), y = b.get(i);
            if (!x.voie().equals(y.voie()) || !x.cp().equals(y.cp()) || !x.ville().equals(y.ville())) {
                return false;
            }
        }
        return true;
    }

    private static Stat stat(List<Double> v) {
        Stat s = new Stat();
        s.n = v.size();
        s.p50 = percentile(v, 50);
        s.p95 = percentile(v, 95);
        s.p99 = percentile(v, 99);
        double sum = 0;
        for (double x : v) sum += x;
        s.mean = v.isEmpty() ? 0.0 : sum / v.size();
        return s;
    }

    private static double percentile(List<Double> v, double p) {
        if (v.isEmpty()) return 0.0;
        List<Double> s = new ArrayList<>(v);
        Collections.sort(s);
        int idx = (int) Math.ceil(p / 100.0 * s.size()) - 1;
        idx = Math.max(0, Math.min(s.size() - 1, idx));
        return s.get(idx);
    }

    /** Nombre de mots d'une requête (même règle que la v1 : split sur espaces). */
    private static int wordCount(String query) {
        if (query == null) return 0;
        String t = query.trim();
        return t.isEmpty() ? 0 : t.split("\\s+").length;
    }

    /** Liste de latences pour {@code wc} mots, créée à la demande. */
    private static List<Double> bucket(Map<Integer, List<Double>> m, int wc) {
        List<Double> l = m.get(wc);
        if (l == null) {
            l = new ArrayList<>();
            m.put(wc, l);
        }
        return l;
    }

    /** Fusionne les deux ventilations en une liste triée (p50/p99 par moteur). */
    private static List<WcStat> wordCountStats(Map<Integer, List<Double>> parByWc,
                                               Map<Integer, List<Double>> seqByWc) {
        List<WcStat> out = new ArrayList<>(parByWc.size());
        for (Map.Entry<Integer, List<Double>> e : parByWc.entrySet()) {
            int wc = e.getKey();
            List<Double> p = e.getValue();
            List<Double> s = seqByWc.get(wc);
            WcStat w = new WcStat();
            w.words = wc;
            w.n = p.size();
            w.parP50 = percentile(p, 50);
            w.parP99 = percentile(p, 99);
            w.seqP50 = percentile(s, 50);
            w.seqP99 = percentile(s, 99);
            out.add(w);
        }
        return out;
    }

    private static void tick(Progress p, int done, int total, String phase) {
        if (p == null) return;
        int step = Math.max(1, total / 100);
        if (done == total || done % step == 0) {
            p.onProgress(done, total, phase);
        }
    }
}
