package com.example.bano.bench;

import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.example.bano.IndexAssets;
import com.example.bano.R;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Écran de benchmark on-device : compare le moteur Rust (JNI) et le moteur Java pur. */
public class BenchmarkActivity extends AppCompatActivity {

    private static final int LIMIT = 10;
    private static final int WARMUP = 200;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private TextView status;
    private LinearLayout results;
    private ProgressBar progress;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_benchmark);

        status = findViewById(R.id.status);
        results = findViewById(R.id.resultsContainer);
        progress = findViewById(R.id.progress);
        Button run = findViewById(R.id.runButton);
        run.setOnClickListener(v -> {
            run.setEnabled(false);
            results.removeAllViews();
            status.setText("Préparation de l'index…");
            progress.setProgress(0);
            progress.setVisibility(View.VISIBLE);
            executor.submit(this::runBenchmark);
        });
    }

    private void runBenchmark() {
        try {
            File dir = IndexAssets.copyIfNeeded(this);
            ui.post(() -> status.setText("Benchmark en cours (warmup " + WARMUP + ")…"));

            BenchRunner runner = new BenchRunner(dir.getAbsolutePath(), getAssets());
            BenchRunner.BenchResult res = runner.run(LIMIT, WARMUP, (done, total, phase) -> {
                int pct = (int) (100L * done / total);
                ui.post(() -> {
                    progress.setProgress(pct);
                    status.setText(String.format("%s… %d / %d (%d%%)", phase, done, total, pct));
                });
            });

            writeReport(res);
            ui.post(() -> {
                progress.setVisibility(View.GONE);
                showResults(res);
                ((Button) findViewById(R.id.runButton)).setEnabled(true);
            });
        } catch (Exception e) {
            ui.post(() -> {
                status.setText("Erreur : " + e.getMessage());
                progress.setVisibility(View.GONE);
                ((Button) findViewById(R.id.runButton)).setEnabled(true);
            });
        }
    }

    // ---------------------------------------------------------------- affichage

    private void showResults(BenchRunner.BenchResult r) {
        BenchRunner.EngineReport ru = r.rust, tr = r.trie, fs = r.fst;
        status.setText(String.format(
                "BANO bench · %d requêtes   ·   parité≡Rust : Trie %.1f %% / FST %.1f %%   ·   timeouts(>3 s) T%d F%d",
                ru.nQueries, r.trieParity * 100.0, r.fstParity * 100.0, r.trieTimeouts, r.fstTimeouts));

        results.removeAllViews();

        // 1) Latence par moteur.
        results.addView(sectionTitle("Latence (ms)"));
        results.addView(hScroll(table(
                new String[]{"moteur", "p50", "p95", "p99", "load"},
                new String[][]{
                        {"Rust (fst)", n(ru.p50), n(ru.p95), n(ru.p99), n(ru.loadMs)},
                        {"Java (Trie)", n(tr.p50), n(tr.p95), n(tr.p99), n(tr.loadMs)},
                        {"Java (FST)", n(fs.p50), n(fs.p95), n(fs.p99), n(fs.loadMs)},
                        {"Trie / Rust", x(tr.p50, ru.p50), x(tr.p95, ru.p95), x(tr.p99, ru.p99), "—"},
                        {"FST / Rust", x(fs.p50, ru.p50), x(fs.p95, ru.p95), x(fs.p99, ru.p99), "—"},
                        {"FST / Trie", x(fs.p50, tr.p50), x(fs.p95, tr.p95), x(fs.p99, tr.p99), "—"},
                }, 1)));

        // 2) Qualité.
        results.addView(sectionTitle("Qualité"));
        results.addView(hScroll(table(
                new String[]{"moteur", "recall@5", "recall@10", "MRR"},
                new String[][]{
                        {"Rust (fst)", n3(ru.recall5), n3(ru.recall10), n3(ru.mrr)},
                        {"Java (Trie)", n3(tr.recall5), n3(tr.recall10), n3(tr.mrr)},
                        {"Java (FST)", n3(fs.recall5), n3(fs.recall10), n3(fs.mrr)},
                }, 1)));

        // 3) Latence par nombre de mots (R=Rust, T=Trie, F=FST).
        results.addView(sectionTitle("Latence par nombre de mots"));
        results.addView(hScroll(wordCountTable(ru, tr, fs)));
    }

    /** Enveloppe une table dans un scroll horizontal (lisible sur petit écran). */
    private android.widget.HorizontalScrollView hScroll(View child) {
        android.widget.HorizontalScrollView hs = new android.widget.HorizontalScrollView(this);
        hs.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        hs.addView(child);
        return hs;
    }

    private TableLayout wordCountTable(BenchRunner.EngineReport ru, BenchRunner.EngineReport tr,
                                       BenchRunner.EngineReport fs) {
        java.util.TreeMap<Integer, BenchRunner.WordCountStat> rByWc = byWords(ru.byWordCount);
        java.util.TreeMap<Integer, BenchRunner.WordCountStat> tByWc = byWords(tr.byWordCount);
        java.util.TreeMap<Integer, BenchRunner.WordCountStat> fByWc = byWords(fs.byWordCount);
        java.util.TreeSet<Integer> words = new java.util.TreeSet<>(rByWc.keySet());
        words.addAll(tByWc.keySet());
        words.addAll(fByWc.keySet());

        java.util.List<String[]> rows = new java.util.ArrayList<>();
        for (int w : words) {
            BenchRunner.WordCountStat r = rByWc.get(w);
            BenchRunner.WordCountStat t = tByWc.get(w);
            BenchRunner.WordCountStat f = fByWc.get(w);
            int n = r != null ? r.n : (t != null ? t.n : (f != null ? f.n : 0));
            rows.add(new String[]{
                    String.valueOf(w), String.valueOf(n),
                    r != null ? n(r.p50) : "—", r != null ? n(r.p99) : "—",
                    t != null ? n(t.p50) : "—", t != null ? n(t.p99) : "—",
                    f != null ? n(f.p50) : "—", f != null ? n(f.p99) : "—",
            });
        }
        return table(
                new String[]{"mots", "n", "R p50", "R p99", "T p50", "T p99", "F p50", "F p99"},
                rows.toArray(new String[0][]), 1);
    }

    // ---------------------------------------------------------------- vues

    /** Construit un TableLayout : 1re ligne = en-tête, cellules >= {@code firstDataCol} alignées à droite. */
    private TableLayout table(String[] headers, String[][] rows, int firstDataCol) {
        TableLayout t = new TableLayout(this);
        t.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        t.setStretchAllColumns(true);

        TableRow head = new TableRow(this);
        for (int c = 0; c < headers.length; c++) {
            head.addView(cell(headers[c], true, c >= firstDataCol));
        }
        t.addView(head);

        for (String[] row : rows) {
            TableRow tr = new TableRow(this);
            for (int c = 0; c < row.length; c++) {
                tr.addView(cell(row[c], false, c >= firstDataCol));
            }
            t.addView(tr);
        }
        return t;
    }

    private TextView cell(String text, boolean header, boolean rightAlign) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        tv.setTextColor(header ? Color.parseColor("#FFE3E8F0") : Color.parseColor("#FFCDD3DA"));
        if (header) tv.setTypeface(Typeface.DEFAULT_BOLD);
        tv.setBackgroundResource(header ? R.drawable.bench_cell_header : R.drawable.bench_cell);
        int padH = dp(10), padV = dp(7);
        tv.setPadding(padH, padV, padH, padV);
        tv.setGravity(rightAlign ? (Gravity.END | Gravity.CENTER_VERTICAL)
                : (Gravity.START | Gravity.CENTER_VERTICAL));
        return tv;
    }

    private TextView sectionTitle(String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        tv.setTypeface(Typeface.DEFAULT_BOLD);
        tv.setTextColor(Color.parseColor("#FF8AB4F8"));
        tv.setPadding(0, dp(16), 0, dp(6));
        return tv;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    // ---------------------------------------------------------------- helpers

    private static java.util.TreeMap<Integer, BenchRunner.WordCountStat> byWords(
            java.util.List<BenchRunner.WordCountStat> stats) {
        java.util.TreeMap<Integer, BenchRunner.WordCountStat> m = new java.util.TreeMap<>();
        if (stats != null) {
            for (BenchRunner.WordCountStat s : stats) m.put(s.words, s);
        }
        return m;
    }

    private static String n(double v) {
        return String.format("%.2f", v);
    }

    private static String n3(double v) {
        return String.format("%.3f", v);
    }

    /** Rapport Java÷Rust en "×", ou "—" si non comparable. */
    private static String x(double java, double rust) {
        return rust <= 0 ? "—" : String.format("%.1f×", java / rust);
    }

    private void writeReport(BenchRunner.BenchResult r) throws Exception {
        JSONArray reports = new JSONArray();
        reports.put(engineJson(r.rust));
        reports.put(engineJson(r.trie));
        reports.put(engineJson(r.fst));
        JSONObject root = new JSONObject();
        root.put("reports", reports);
        root.put("trie_parity_ok", r.trieParity);
        root.put("fst_parity_ok", r.fstParity);
        root.put("trie_timeouts", r.trieTimeouts);
        root.put("fst_timeouts", r.fstTimeouts);

        File out = new File(getFilesDir(), "bench_report.json");
        try (OutputStream os = new FileOutputStream(out)) {
            os.write(root.toString(2).getBytes(StandardCharsets.UTF_8));
        }
    }

    private static JSONObject engineJson(BenchRunner.EngineReport e) throws Exception {
        JSONObject o = new JSONObject();
        o.put("name", e.name);
        o.put("load_ms", e.loadMs);
        o.put("latency_p50_ms", e.p50);
        o.put("latency_p95_ms", e.p95);
        o.put("latency_p99_ms", e.p99);
        o.put("recall_at_5", e.recall5);
        o.put("recall_at_10", e.recall10);
        o.put("mrr", e.mrr);
        o.put("n_queries", e.nQueries);
        JSONArray byWc = new JSONArray();
        if (e.byWordCount != null) {
            for (BenchRunner.WordCountStat s : e.byWordCount) {
                JSONObject w = new JSONObject();
                w.put("words", s.words);
                w.put("n", s.n);
                w.put("latency_p50_ms", s.p50);
                w.put("latency_p99_ms", s.p99);
                byWc.put(w);
            }
        }
        o.put("by_word_count", byWc);
        return o;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }
}
