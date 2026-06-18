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

import com.example.bano.bench.BenchmarkActivity;
import com.example.bano.pure.PureIndex;

import java.io.File;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Écran unique : un switch Rust/Java, un champ de recherche, une liste de
 * résultats. À chaque frappe (débouncée ~80 ms), on interroge le moteur
 * sélectionné hors du thread UI. Un bouton ouvre l'écran de benchmark.
 */
public class MainActivity extends AppCompatActivity {

    private static final long DEBOUNCE_MS = 80L;
    private static final long JAVA_DEADLINE_NS = 2_000_000_000L; // borne la recherche Java live

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private BanoFst rust;
    private PureIndex java;
    private boolean useJava;

    private ResultAdapter adapter;
    private TextView status;
    private EditText field;
    private Runnable pending;

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
            useJava = checked;
            v.setText(checked ? "Moteur : Java" : "Moteur : Rust");
            // Relance immédiate avec le nouveau moteur sur la requête courante.
            runSearch(field.getText().toString());
        });

        Button bench = findViewById(R.id.benchButton);
        bench.setOnClickListener(v ->
                startActivity(new Intent(this, BenchmarkActivity.class)));

        // Ouverture des deux index hors UI thread (copie assets au 1er lancement).
        status.setText("Chargement des index…");
        executor.submit(() -> {
            try {
                File dir = IndexAssets.copyIfNeeded(this);
                BanoFst openedRust = new BanoFst(dir.getAbsolutePath());
                PureIndex openedJava = PureIndex.open(dir.getAbsolutePath());
                ui.post(() -> {
                    rust = openedRust;
                    java = openedJava;
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
        if (rust == null || java == null) {
            return;
        }
        boolean wantJava = useJava;
        String engineName = wantJava ? "Java" : "Rust";
        executor.submit(() -> {
            long t0 = System.nanoTime();
            List<Result> hits;
            try {
                hits = wantJava
                        ? java.search(query, 10, t0 + JAVA_DEADLINE_NS)
                        : rust.search(query, 10);
            } catch (PureIndex.TimeoutException | OutOfMemoryError e) {
                ui.post(() -> status.setText("Java a abandonné (trop lent/mémoire) — requête plus précise"));
                return;
            }
            double ms = (System.nanoTime() - t0) / 1_000_000.0;
            List<Result> finalHits = hits;
            ui.post(() -> {
                adapter.submit(finalHits);
                status.setText(String.format("%s — %d résultat(s) — %.2f ms",
                        engineName, finalHits.size(), ms));
            });
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (rust != null) {
            rust.close();
            rust = null;
        }
        if (java != null) {
            java.close();
            java = null;
        }
        executor.shutdownNow();
    }
}
