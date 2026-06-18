package com.example.bano.pure;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import org.junit.Test;

public class FlatTrieTest {

    private static FlatTrie build(String... tokens) {
        FlatTrie.Builder b = new FlatTrie.Builder();
        for (int i = 0; i < tokens.length; i++) b.insert(tokens[i], i);
        return b.build();
    }

    private static List<Integer> subtreeLeaves(FlatTrie t, int node) {
        List<Integer> out = new ArrayList<>();
        for (int i = node; i < t.subtreeEnd[node]; i++) {
            if (t.leaf[i] >= 0) out.add(t.leaf[i]);
        }
        Collections.sort(out);
        return out;
    }

    @Test public void prefixeCollecteSousArbre() {
        FlatTrie t = build("paris", "parc", "bourg");
        int node = FlatTrie.ROOT;
        for (int c : "par".codePoints().toArray()) {
            node = t.child(node, c);
            assertTrue("descente 'par' existe", node >= 0);
        }
        assertEquals(Arrays.asList(0, 1), subtreeLeaves(t, node));
    }

    @Test public void descenteInconnueRendMoinsUn() {
        FlatTrie t = build("paris");
        assertEquals(-1, t.child(FlatTrie.ROOT, 'z'));
    }

    @Test public void feuilleInterneEtSousArbre() {
        // "par" est à la fois feuille et préfixe de "paris".
        FlatTrie t = build("par", "paris");
        int node = FlatTrie.ROOT;
        for (int c : "par".codePoints().toArray()) node = t.child(node, c);
        assertTrue(node >= 0);
        assertEquals(0, t.leaf[node]);
        assertEquals(Arrays.asList(0, 1), subtreeLeaves(t, node));
    }

    @Test public void racineCouvreTout() {
        FlatTrie t = build("a", "b", "cd");
        assertEquals(Arrays.asList(0, 1, 2), subtreeLeaves(t, FlatTrie.ROOT));
    }
}
