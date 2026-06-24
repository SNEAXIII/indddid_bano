package com.example.bano;

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
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * banorust — benchmark on-device : compare les DEUX moteurs Rust (parallèle/rayon
 * vs séquentiel) sur le jeu de requêtes. Affiche p50/p95/p99/moyenne et le
 * speedup dans un tableau, plus un contrôle de parité (résultats identiques).
 */
public class BenchmarkActivity extends AppCompatActivity {

    private static final int LIMIT = 10;
    private static final int WARMUP = 200;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private TextView status;
    private LinearLayout results;
    private ProgressBar progress;
    private Button run;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(12);
        root.setPadding(pad, pad, pad, pad);

        run = new Button(this);
        run.setText("Lancer le benchmark");
        root.addView(run);

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        progress.setVisibility(View.GONE);
        root.addView(progress);

        status = new TextView(this);
        status.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        status.setPadding(0, dp(6), 0, dp(6));
        status.setText("Appuyez sur « Lancer » (warmup " + WARMUP + ").");
        root.addView(status);

        results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        ScrollView scroll = new ScrollView(this);
        scroll.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        scroll.addView(results);
        root.addView(scroll);

        setContentView(root);

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

            CompareBench bench = new CompareBench(dir.getAbsolutePath(), getAssets());
            CompareBench.Outcome o = bench.run(LIMIT, WARMUP, (done, total, phase) -> {
                int pct = (int) (100L * done / total);
                ui.post(() -> {
                    progress.setProgress(pct);
                    status.setText(String.format(Locale.US, "%s… %d / %d (%d%%)", phase, done, total, pct));
                });
            });

            ui.post(() -> {
                progress.setVisibility(View.GONE);
                showResults(o);
                run.setEnabled(true);
            });
        } catch (Exception e) {
            ui.post(() -> {
                status.setText("Erreur : " + e.getMessage());
                progress.setVisibility(View.GONE);
                run.setEnabled(true);
            });
        }
    }

    // ---------------------------------------------------------------- affichage

    private void showResults(CompareBench.Outcome o) {
        String parity = o.mismatches == 0
                ? "parité OK (0 écart)"
                : ("⚠ " + o.mismatches + " écart(s) !");
        status.setText(String.format(Locale.US, "banorust bench · %d requêtes · %s", o.nQueries, parity));

        CompareBench.Stat p = o.parallel, s = o.seq;

        results.removeAllViews();
        results.addView(sectionTitle("Latence (ms)"));
        results.addView(hScroll(table(
                new String[]{"moteur", "p50", "p95", "p99", "moy"},
                new String[][]{
                        {"Parallèle", n(p.p50), n(p.p95), n(p.p99), n(p.mean)},
                        {"Séquentiel", n(s.p50), n(s.p95), n(s.p99), n(s.mean)},
                        {"speedup", x(s.p50, p.p50), x(s.p95, p.p95), x(s.p99, p.p99), x(s.mean, p.mean)},
                }, 1)));

        TextView note = new TextView(this);
        note.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        note.setTextColor(Color.parseColor("#FF9AA0A6"));
        note.setPadding(0, dp(8), 0, 0);
        note.setText("speedup = séquentiel ÷ parallèle (> 1× : le parallèle est plus rapide)");
        results.addView(note);
    }

    // ---------------------------------------------------------------- vues (portées de :app)

    private HorizontalScrollView hScroll(View child) {
        HorizontalScrollView hs = new HorizontalScrollView(this);
        hs.setLayoutParams(new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        hs.addView(child);
        return hs;
    }

    /** TableLayout : 1re ligne = en-tête, cellules >= {@code firstDataCol} alignées à droite. */
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
        int padH = dp(12), padV = dp(8);
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
        tv.setPadding(0, dp(12), 0, dp(6));
        return tv;
    }

    private static String n(double v) {
        return String.format(Locale.US, "%.2f", v);
    }

    private static String x(double seq, double par) {
        return par <= 0 ? "—" : String.format(Locale.US, "%.2f×", seq / par);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        executor.shutdownNow();
    }
}
