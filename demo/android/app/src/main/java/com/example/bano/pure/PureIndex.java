package com.example.bano.pure;

import com.example.bano.Result;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Moteur Java pur. Port de index.rs : union(préfixe, automate Levenshtein) par
 * jeton, intersection ET en sommant les poids, tri (score desc, rid asc), décodage.
 *
 * Optimisé sans changer l'algorithme ni les résultats : trie aplati en arrays
 * ({@link FlatTrie}, sous-arbre = plage préordre contiguë), bitset pour les
 * jetons matchés, maps primitives int-&gt;float ({@link IntFloatMap}), lignes DP
 * réutilisées par profondeur, tri primitif sur clés packées (score desc, rid asc).
 */
public final class PureIndex implements AutoCloseable {
    private final Vocab vocab;
    private final Postings postings;
    private final Records records;
    private final TokenMatcher matcher;
    private final String[] tokens;

    private PureIndex(Vocab vocab, Postings postings, Records records, TokenMatcher matcher,
                      String[] tokens) {
        this.vocab = vocab;
        this.postings = postings;
        this.records = records;
        this.matcher = matcher;
        this.tokens = tokens;
    }

    /** Moteur d'origine : trie aplati maison ({@link FlatTrieMatcher}). */
    public static PureIndex open(String dir) throws IOException {
        return open(dir, false);
    }

    /** Variante FST Lucene ({@link FstMatcher}) — mêmes résultats, structure différente. */
    public static PureIndex openFst(String dir) throws IOException {
        return open(dir, true);
    }

    private static PureIndex open(String dir, boolean useFst) throws IOException {
        ByteBuffer vb = MmapReader.map(dir + "/vocab.bin");
        ByteBuffer pb = MmapReader.map(dir + "/postings.bin");
        ByteBuffer rb = MmapReader.map(dir + "/records.bin");
        Vocab vocab = new Vocab(vb);
        String[] tokens = vocab.allTokens();
        TokenMatcher matcher;
        if (useFst) {
            // Prébuild Gradle (lucene.fst) si présent -> chargement direct ;
            // sinon reconstruction en RAM depuis les jetons.
            java.io.File fstFile = new java.io.File(dir, "lucene.fst");
            matcher = fstFile.exists() ? new FstMatcher(fstFile) : new FstMatcher(tokens);
        } else {
            matcher = new FlatTrieMatcher(tokens);
        }
        return new PureIndex(vocab, new Postings(pb), new Records(rb), matcher, tokens);
    }

    /** Levée si la recherche dépasse l'échéance (en valeurs System.nanoTime()). */
    public static final class TimeoutException extends RuntimeException {
        public TimeoutException(String m) { super(m); }
    }

    public List<Result> search(String query, int limit) {
        return search(query, limit, Long.MAX_VALUE);
    }

    /** Variante bornée : abandonne (TimeoutException) si {@code System.nanoTime() > deadlineNanos}. */
    public List<Result> search(String query, int limit, long deadlineNanos) {
        List<String> qtokens = Normalize.tokenize(query);
        if (qtokens.isEmpty()) {
            return List.of();
        }

        long[] matched = new long[(tokens.length + 63) >>> 6];
        IntFloatMap[] perToken = new IntFloatMap[qtokens.size()];
        for (int ti = 0; ti < qtokens.size(); ti++) {
            String qtok = qtokens.get(ti);
            if (ti > 0) Arrays.fill(matched, 0L);
            int d = qtok.codePointCount(0, qtok.length()) <= 4 ? 1 : 2;

            matcher.match(qtok, d, matched, deadlineNanos);

            IntFloatMap scores = new IntFloatMap(64);
            int guard = 0;
            for (int wi = 0; wi < matched.length; wi++) {
                long word = matched[wi];
                while (word != 0) {
                    int vi = (wi << 6) + Long.numberOfTrailingZeros(word);
                    word &= word - 1;
                    float w = Levenshtein.similarity(qtok, tokens[vi]);
                    long packed = vocab.packed(vi);
                    long off = packed >>> 32;
                    long len = packed & 0xFFFFFFFFL;
                    for (long k = 0; k < len; k++) {
                        if ((++guard & 1023) == 0 && System.nanoTime() > deadlineNanos) {
                            throw new TimeoutException("search deadline (postings) q=" + query);
                        }
                        scores.maxPut(postings.rid(off + k), w);
                    }
                }
            }
            perToken[ti] = scores;
        }

        IntFloatMap acc = perToken[0];
        for (int t = 1; t < perToken.length; t++) {
            if (System.nanoTime() > deadlineNanos) {
                throw new TimeoutException("search deadline (merge) q=" + query);
            }
            IntFloatMap next = perToken[t];
            IntFloatMap merged = new IntFloatMap(Math.min(acc.size(), next.size()));
            int[] keys = acc.keysRaw();
            float[] vals = acc.valsRaw();
            for (int i = 0; i < keys.length; i++) {
                int rid = keys[i];
                if (rid == IntFloatMap.EMPTY) continue;
                float w2 = next.get(rid, Float.NaN);
                if (w2 == w2) {
                    merged.put(rid, vals[i] + w2);
                }
            }
            acc = merged;
        }

        // Tri primitif : clé = (bits de score inversés) << 32 | rid. Les scores sont
        // des float >= 0 (jamais NaN), donc l'ordre des bits suit l'ordre des valeurs ;
        // le tri ascendant donne score desc puis rid asc, comme le comparateur d'origine.
        long[] order = new long[acc.size()];
        int oi = 0;
        int[] keys = acc.keysRaw();
        float[] vals = acc.valsRaw();
        for (int i = 0; i < keys.length; i++) {
            if (keys[i] == IntFloatMap.EMPTY) continue;
            long inv = 0xFFFFFFFFL - (Float.floatToRawIntBits(vals[i]) & 0xFFFFFFFFL);
            order[oi++] = (inv << 32) | (keys[i] & 0xFFFFFFFFL);
        }
        Arrays.sort(order);

        int max = Math.min(limit, order.length);
        List<Result> out = new ArrayList<>(max);
        for (int i = 0; i < max; i++) {
            int rid = (int) order[i];
            float score = Float.intBitsToFloat((int) (0xFFFFFFFFL - (order[i] >>> 32)));
            String[] rec = records.record(rid);
            out.add(new Result(score, rec[0], rec[1], rec[2]));
        }
        return out;
    }

    @Override
    public void close() {
        // Les MappedByteBuffer sont libérés par le GC ; rien d'explicite.
        try {
            matcher.close();
        } catch (Exception ignored) {
            // close() des matchers ne lève rien en pratique.
        }
    }
}
