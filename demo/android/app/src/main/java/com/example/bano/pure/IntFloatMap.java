package com.example.bano.pure;

import java.util.Arrays;

/**
 * Map int -&gt; float en adressage ouvert (sondage linéaire), clés &gt;= 0.
 * Remplace HashMap&lt;Integer, Float&gt; dans les chemins chauds : zéro boxing,
 * zéro nœud d'entrée, accès contigus.
 */
final class IntFloatMap {
    static final int EMPTY = -1;

    private int[] keys;
    private float[] vals;
    private int mask;
    private int size;

    IntFloatMap(int expected) {
        int cap = 8;
        while (cap < expected * 2) cap <<= 1;
        keys = new int[cap];
        vals = new float[cap];
        Arrays.fill(keys, EMPTY);
        mask = cap - 1;
    }

    int size() {
        return size;
    }

    private int slot(int key) {
        int h = key * 0x9E3779B9;
        return (h ^ (h >>> 16)) & mask;
    }

    float get(int key, float def) {
        int i = slot(key);
        while (true) {
            int k = keys[i];
            if (k == key) return vals[i];
            if (k == EMPTY) return def;
            i = (i + 1) & mask;
        }
    }

    void put(int key, float v) {
        int i = slot(key);
        while (true) {
            int k = keys[i];
            if (k == key) {
                vals[i] = v;
                return;
            }
            if (k == EMPTY) {
                keys[i] = key;
                vals[i] = v;
                if (++size * 3 > keys.length * 2) grow();
                return;
            }
            i = (i + 1) & mask;
        }
    }

    /** Insère, ou garde le max si la clé existe déjà (sémantique des scores par jeton). */
    void maxPut(int key, float v) {
        int i = slot(key);
        while (true) {
            int k = keys[i];
            if (k == key) {
                if (v > vals[i]) vals[i] = v;
                return;
            }
            if (k == EMPTY) {
                keys[i] = key;
                vals[i] = v;
                if (++size * 3 > keys.length * 2) grow();
                return;
            }
            i = (i + 1) & mask;
        }
    }

    /** Accès brut pour itération : entrées valides là où keysRaw()[i] != EMPTY. */
    int[] keysRaw() {
        return keys;
    }

    float[] valsRaw() {
        return vals;
    }

    private void grow() {
        int[] ok = keys;
        float[] ov = vals;
        int cap = ok.length << 1;
        keys = new int[cap];
        vals = new float[cap];
        Arrays.fill(keys, EMPTY);
        mask = cap - 1;
        size = 0;
        for (int i = 0; i < ok.length; i++) {
            if (ok[i] != EMPTY) put(ok[i], ov[i]);
        }
    }
}
