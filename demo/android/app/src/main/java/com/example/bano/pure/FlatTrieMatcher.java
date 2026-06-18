package com.example.bano.pure;

/**
 * {@link TokenMatcher} d'origine : trie aplati maison ({@link FlatTrie}).
 * Code extrait tel quel de PureIndex (DFS Levenshtein guidé par ligne DP +
 * collecte de préfixe par balayage de la plage préordre). Comportement inchangé.
 */
public final class FlatTrieMatcher implements TokenMatcher {
    private final FlatTrie trie;

    public FlatTrieMatcher(String[] tokens) {
        FlatTrie.Builder builder = new FlatTrie.Builder();
        for (int i = 0; i < tokens.length; i++) {
            builder.insert(tokens[i], i);
        }
        this.trie = builder.build();
    }

    @Override
    public void match(String qtok, int maxDist, long[] matched, long deadlineNanos) {
        int[] qcps = qtok.codePoints().toArray();
        new LevWalker(qcps, maxDist, matched, deadlineNanos).walk(FlatTrie.ROOT, 1);

        int node = FlatTrie.ROOT;
        for (int i = 0; i < qcps.length && node >= 0; i++) {
            node = trie.child(node, qcps[i]);
        }
        if (node >= 0) {
            markSubtree(node, matched, deadlineNanos);
        }
    }

    /**
     * DFS du trie guidé par une ligne DP Levenshtein ; élagage si min(row) > maxDist.
     * Lignes DP allouées une fois par profondeur, réutilisées entre frères.
     */
    private final class LevWalker {
        private final int[] qcps;
        private final int maxDist;
        private final long[] matched;
        private final long deadline;
        private final int[][] rows;
        private int guard;

        LevWalker(int[] qcps, int maxDist, long[] matched, long deadline) {
            this.qcps = qcps;
            this.maxDist = maxDist;
            this.matched = matched;
            this.deadline = deadline;
            this.rows = new int[qcps.length + maxDist + 2][];
            int[] init = new int[qcps.length + 1];
            for (int j = 0; j <= qcps.length; j++) init[j] = j;
            rows[0] = init;
        }

        void walk(int node, int depth) {
            int cols = qcps.length;
            int[] prev = rows[depth - 1];
            int[] curr = rows[depth];
            if (curr == null) {
                curr = new int[cols + 1];
                rows[depth] = curr;
            }
            int start = trie.childStart[node];
            int end = start + trie.childCount[node];
            for (int ci = start; ci < end; ci++) {
                if ((++guard & 255) == 0 && System.nanoTime() > deadline) {
                    throw new PureIndex.TimeoutException("search deadline (levenshtein walk)");
                }
                int cp = trie.childCp[ci];
                curr[0] = depth;
                int rowMin = depth;
                for (int j = 1; j <= cols; j++) {
                    int cost = (qcps[j - 1] == cp) ? 0 : 1;
                    int v = Math.min(Math.min(prev[j] + 1, curr[j - 1] + 1), prev[j - 1] + cost);
                    curr[j] = v;
                    if (v < rowMin) rowMin = v;
                }
                int child = trie.childNode[ci];
                int lf = trie.leaf[child];
                if (lf >= 0 && curr[cols] <= maxDist) {
                    matched[lf >>> 6] |= 1L << lf;
                }
                if (rowMin <= maxDist) {
                    walk(child, depth + 1);
                }
            }
        }
    }

    /** Marque les feuilles du sous-arbre : balayage de la plage préordre contiguë. */
    private void markSubtree(int node, long[] matched, long deadlineNanos) {
        int end = trie.subtreeEnd[node];
        int guard = 0;
        for (int i = node; i < end; i++) {
            if ((++guard & 8191) == 0 && System.nanoTime() > deadlineNanos) {
                throw new PureIndex.TimeoutException("search deadline (subtree)");
            }
            int lf = trie.leaf[i];
            if (lf >= 0) {
                matched[lf >>> 6] |= 1L << lf;
            }
        }
    }
}
