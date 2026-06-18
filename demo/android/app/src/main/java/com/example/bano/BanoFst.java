package com.example.bano;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Pont Java vers la bibliothèque native Rust `bano-fst`.
 *
 * <p>Le {@code System.loadLibrary("bano_fst")} charge {@code libbano_fst.so}
 * (compilé par cargo-ndk dans jniLibs/&lt;abi&gt;/). Les 3 méthodes natives se
 * mappent sur les fonctions JNI du module Rust {@code jni_bridge.rs}.</p>
 */
public final class BanoFst implements AutoCloseable {

    static {
        System.loadLibrary("bano_fst");
    }

    /** Handle natif (pointeur vers le Box&lt;Index&gt; Rust). 0 = non ouvert. */
    private long handle;

    private static native long nativeOpen(String dir);

    private static native String nativeSearch(long handle, String query, int limit);

    private static native void nativeClose(long handle);

    /**
     * Ouvre un index (dossier contenant index.fst / postings.bin / records.bin).
     *
     * @throws IllegalStateException si l'ouverture échoue (fichiers manquants).
     */
    public BanoFst(String indexDir) {
        this.handle = nativeOpen(indexDir);
        if (this.handle == 0) {
            throw new IllegalStateException("Ouverture de l'index échouée : " + indexDir);
        }
    }

    /** Recherche floue. Renvoie une liste (éventuellement vide) de résultats. */
    public List<Result> search(String query, int limit) {
        if (handle == 0 || query == null || query.isBlank()) {
            return List.of();
        }
        String json = nativeSearch(handle, query, limit);
        return parse(json);
    }

    private static List<Result> parse(String json) {
        List<Result> out = new ArrayList<>();
        if (json == null || json.isEmpty()) {
            return out;
        }
        try {
            JSONArray arr = new JSONArray(json);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject o = arr.getJSONObject(i);
                out.add(new Result(
                        o.optDouble("score", 0.0),
                        o.optString("voie", ""),
                        o.optString("cp", ""),
                        o.optString("ville", "")));
            }
        } catch (Exception e) {
            // JSON malformé : on renvoie ce qu'on a (ne crashe pas l'UI).
        }
        return out;
    }

    @Override
    public void close() {
        if (handle != 0) {
            nativeClose(handle);
            handle = 0;
        }
    }
}
