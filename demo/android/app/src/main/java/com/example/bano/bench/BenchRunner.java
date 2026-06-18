package com.example.bano.bench;

import android.content.res.AssetManager;
import android.util.Log;

import com.example.bano.BanoFst;
import com.example.bano.Result;
import com.example.bano.pure.PureIndex;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Exécute les deux moteurs (Rust JNI, Java pur) sur le même jeu de requêtes, dans
 * le même process, entrelacés, avec warmup. Mesure latence/recall/MRR + parité.
 */
public final class BenchRunner {

    public static final class EngineReport {
        public String name;
        public double loadMs;
        public double p50, p95, p99;
        public double recall5, recall10, mrr;
        public int nQueries;
        /** Latence par nombre de mots de la requête, trié croissant. */
        public List<WordCountStat> byWordCount;
    }

    /** Stats de latence pour les requêtes ayant {@code words} mots. */
    public static final class WordCountStat {
        public int words;
        public int n;
        public double p50, p99;
    }

    public static final class BenchResult {
        public EngineReport rust;
        public EngineReport trie;       // Java, trie aplati maison
        public EngineReport fst;        // Java, FST Lucene
        public double trieParity;       // fraction de requêtes identiques à Rust
        public double fstParity;
        public int trieTimeouts;
        public int fstTimeouts;
    }

    /** Accumulateur de mesures pour un moteur (latence, qualité, parité). */
    private static final class Acc {
        final List<Double> lat = new ArrayList<>();
        final List<Double> r5 = new ArrayList<>(), r10 = new ArrayList<>(), rr = new ArrayList<>();
        final Map<Integer, List<Double>> byWc = new TreeMap<>();
        int timeouts = 0;
        int parity = 0;
    }

    /** Rappel de progression : {@code done}/{@code total} étapes, {@code phase} = libellé. */
    public interface Progress {
        void onProgress(int done, int total, String phase);
    }

    /** Au-delà, une recherche Java est abandonnée et la requête marquée "timeout". */
    private static final long JAVA_DEADLINE_NS = 3_000_000_000L; // 3 s

    private final String indexDir;
    private final AssetManager assets;

    public BenchRunner(String indexDir, AssetManager assets) {
        this.indexDir = indexDir;
        this.assets = assets;
    }

    private List<JSONObject> loadQueries() throws Exception {
        try (InputStream in = assets.open("bench/queries.json")) {
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] b = new byte[1 << 16];
            int n;
            while ((n = in.read(b)) > 0) bos.write(b, 0, n);
            JSONArray arr = new JSONArray(new String(bos.toByteArray(), StandardCharsets.UTF_8));
            List<JSONObject> out = new ArrayList<>(arr.length());
            for (int i = 0; i < arr.length(); i++) out.add(arr.getJSONObject(i));
            return out;
        }
    }

    public BenchResult run(int limit, int warmup) throws Exception {
        return run(limit, warmup, null);
    }

    public BenchResult run(int limit, int warmup, Progress progress) throws Exception {
        List<JSONObject> queries = loadQueries();
        int w0 = Math.min(warmup, queries.size());
        int total = w0 + queries.size();

        long t0 = System.nanoTime();
        BanoFst rust = new BanoFst(indexDir);
        double rustLoad = (System.nanoTime() - t0) / 1e6;

        long t1 = System.nanoTime();
        PureIndex trie = PureIndex.open(indexDir);          // trie aplati maison
        double trieLoad = (System.nanoTime() - t1) / 1e6;

        long t2 = System.nanoTime();
        PureIndex fst = PureIndex.openFst(indexDir);         // FST Lucene (prébuild si présent)
        double fstLoad = (System.nanoTime() - t2) / 1e6;

        try {
            for (int i = 0; i < w0; i++) {
                String q = queries.get(i).getString("query");
                rust.search(q, limit);
                warmJava(trie, q, limit);
                warmJava(fst, q, limit);
                tick(progress, i + 1, total, "warmup");
            }

            Acc ra = new Acc(), ta = new Acc(), fa = new Acc();
            int done = 0;
            for (JSONObject item : queries) {
                String q = item.getString("query");
                int wc = BenchMetrics.wordCount(q);
                JSONObject tg = item.getJSONObject("target");
                String voie = tg.getString("voie");
                String cp = tg.getString("code_postal");
                String ville = tg.getString("ville");

                long a = System.nanoTime();
                List<Result> rh = rust.search(q, limit);
                recordHits(ra, (System.nanoTime() - a) / 1e6, wc, rh, voie, cp, ville, null);

                measureJava(trie, q, limit, wc, voie, cp, ville, rh, ta);
                measureJava(fst, q, limit, wc, voie, cp, ville, rh, fa);

                tick(progress, w0 + (++done), total, "mesure");
            }

            BenchResult res = new BenchResult();
            res.rust = report("rust-fst-jni", rustLoad, ra);
            res.trie = report("java-flattrie", trieLoad, ta);
            res.fst = report("java-lucene-fst", fstLoad, fa);
            res.trieParity = (double) ta.parity / Math.max(1, ta.lat.size());
            res.fstParity = (double) fa.parity / Math.max(1, fa.lat.size());
            res.trieTimeouts = ta.timeouts;
            res.fstTimeouts = fa.timeouts;
            return res;
        } finally {
            rust.close();
            trie.close();
            fst.close();
        }
    }

    /** Notifie la progression, ~tous les 1 % (limite le trafic vers l'UI thread). */
    private static void tick(Progress p, int done, int total, String phase) {
        if (p == null) return;
        int step = Math.max(1, total / 100);
        if (done == total || done % step == 0) {
            p.onProgress(done, total, phase);
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

    /** Warmup d'un moteur Java (résultat ignoré, timeout avalé). */
    private static void warmJava(PureIndex eng, String q, int limit) {
        try {
            eng.search(q, limit, System.nanoTime() + JAVA_DEADLINE_NS);
        } catch (PureIndex.TimeoutException | OutOfMemoryError ignored) {
            // une requête abandonnée au warmup n'invalide rien
        }
    }

    /** Mesure une requête sur un moteur Java borné ; compare à Rust pour la parité. */
    private void measureJava(PureIndex eng, String q, int limit, int wc, String voie, String cp,
                             String ville, List<Result> rustHits, Acc acc) {
        long c = System.nanoTime();
        List<Result> jh;
        try {
            jh = eng.search(q, limit, c + JAVA_DEADLINE_NS);
        } catch (PureIndex.TimeoutException | OutOfMemoryError e) {
            acc.timeouts++;
            return;
        }
        recordHits(acc, (System.nanoTime() - c) / 1e6, wc, jh, voie, cp, ville, rustHits);
    }

    /** Range latence + qualité d'une réponse ; si {@code ref} != null, compte la parité. */
    private static void recordHits(Acc acc, double ms, int wc, List<Result> hits, String voie,
                                   String cp, String ville, List<Result> ref) {
        acc.lat.add(ms);
        bucket(acc.byWc, wc).add(ms);
        acc.r5.add(BenchMetrics.recallAtK(hits, voie, cp, ville, 5));
        acc.r10.add(BenchMetrics.recallAtK(hits, voie, cp, ville, 10));
        acc.rr.add(BenchMetrics.reciprocalRank(hits, voie, cp, ville));
        if (ref != null && sameResults(ref, hits)) acc.parity++;
    }

    private static EngineReport report(String name, double load, Acc a) {
        EngineReport e = new EngineReport();
        e.name = name;
        e.loadMs = load;
        e.nQueries = a.lat.size();
        e.p50 = BenchMetrics.percentile(a.lat, 50);
        e.p95 = BenchMetrics.percentile(a.lat, 95);
        e.p99 = BenchMetrics.percentile(a.lat, 99);
        e.recall5 = avg(a.r5);
        e.recall10 = avg(a.r10);
        e.mrr = avg(a.rr);
        e.byWordCount = wordCountStats(a.byWc);
        return e;
    }

    /** Renvoie la liste (mot croissant) du couple p50/p99 par nombre de mots. */
    private static List<WordCountStat> wordCountStats(Map<Integer, List<Double>> latByWc) {
        List<WordCountStat> out = new ArrayList<>(latByWc.size());
        for (Map.Entry<Integer, List<Double>> en : latByWc.entrySet()) {
            WordCountStat s = new WordCountStat();
            s.words = en.getKey();
            s.n = en.getValue().size();
            s.p50 = BenchMetrics.percentile(en.getValue(), 50);
            s.p99 = BenchMetrics.percentile(en.getValue(), 99);
            out.add(s);
        }
        return out;
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

    private static double avg(List<Double> v) {
        if (v.isEmpty()) return 0.0;
        double s = 0;
        for (double x : v) s += x;
        return s / v.size();
    }
}
