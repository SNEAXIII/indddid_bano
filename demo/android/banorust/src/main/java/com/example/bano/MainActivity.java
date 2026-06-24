package com.example.bano;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.SwitchCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.io.File;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Démo 2 — comparaison des DEUX moteurs Rust : recherche séquentielle vs
 * parallèle (rayon). Le switch choisit lequel pilote les résultats affichés
 * (même UX que le switch Rust/Java de l'app principale). Les deux renvoient
 * EXACTEMENT les mêmes résultats ; seule la latence (affichée) change.
 */
public class MainActivity extends AppCompatActivity {

    private static final long DEBOUNCE_MS = 80L;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private BanoFst rust;
    private boolean useSeq;          // false = parallèle (défaut), true = séquentiel

    private ResultAdapter adapter;
    private TextView status;
    private EditText field;
    private Runnable pending;

    // Coalescing : au plus UNE recherche en vol (cf. app principale).
    private boolean searching;
    private String queued;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        status = findViewById(R.id.status);
        adapter = new ResultAdapter();

        RecyclerView results = findViewById(R.id.results);
        results.setLayoutManager(new LinearLayoutManager(this));
        results.setAdapter(adapter);

        field = findViewById(R.id.searchField);
        field.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable s) {
                scheduleSearch(s.toString());
            }
        });

        SwitchCompat engineSwitch = findViewById(R.id.engineSwitch);
        engineSwitch.setOnCheckedChangeListener((v, checked) -> {
            useSeq = checked;
            v.setText(checked ? "Moteur : Séquentiel" : "Moteur : Parallèle (rayon)");
            runSearch(field.getText().toString());
        });

        Button bench = findViewById(R.id.benchButton);
        bench.setOnClickListener(v ->
                startActivity(new Intent(this, BenchmarkActivity.class)));

        status.setText("Chargement de l'index…");
        executor.submit(() -> {
            try {
                File dir = IndexAssets.copyIfNeeded(this);
                BanoFst opened = new BanoFst(dir.getAbsolutePath());
                ui.post(() -> {
                    rust = opened;
                    status.setText("Prêt. Tapez une adresse.");
                });
            } catch (Exception e) {
                ui.post(() -> status.setText("Erreur index : " + e.getMessage()));
            }
        });
    }

    /** Débounce : annule la recherche en attente et en planifie une nouvelle. */
    private void scheduleSearch(String query) {
        if (pending != null) {
            ui.removeCallbacks(pending);
        }
        pending = () -> runSearch(query);
        ui.postDelayed(pending, DEBOUNCE_MS);
    }

    private void runSearch(String query) {
        if (rust == null) {
            return;
        }
        if (searching) {
            queued = query;
            return;
        }
        searching = true;
        dispatchSearch(query);
    }

    /** Exécute la recherche hors UI thread puis enchaîne sur la requête en attente. */
    private void dispatchSearch(String query) {
        boolean seq = useSeq;
        String engineName = seq ? "Séquentiel" : "Parallèle";
        executor.submit(() -> {
            long t0 = System.nanoTime();
            List<Result> hits = seq ? rust.searchSeq(query, 10) : rust.search(query, 10);
            double ms = (System.nanoTime() - t0) / 1_000_000.0;
            List<Result> finalHits = hits;
            ui.post(() -> {
                adapter.submit(finalHits);
                status.setText(String.format("%s — %d résultat(s) — %.2f ms",
                        engineName, finalHits.size(), ms));
                searching = false;
                if (queued != null) {
                    String next = queued;
                    queued = null;
                    runSearch(next);
                }
            });
        });
    }
}
