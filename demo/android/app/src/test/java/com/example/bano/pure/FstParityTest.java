package com.example.bano.pure;

import static org.junit.Assert.assertEquals;

import com.example.bano.Result;
import java.io.File;
import java.util.List;
import org.junit.Test;

/**
 * Parité {@link FlatTrieMatcher} ↔ {@link FstMatcher} : sur le même index, les deux
 * structures doivent rendre EXACTEMENT les mêmes résultats (score, ordre, champs).
 * C'est l'invariant qui justifie l'interchangeabilité du portage Lucene FST.
 */
public class FstParityTest {
    private String miniDir() {
        return new File("src/test/resources/mini").getAbsolutePath();
    }

    private static final String[] QUERIES = {
            "paris", "pari", "par", "pa", "rue", "ru", "paix", "pai",
            "boulevard", "75002", "rue paix", "rue de la paix", "xyz", "rue paxi",
    };

    @Test public void memeResultatsTrieEtFst() throws Exception {
        try (PureIndex trie = PureIndex.open(miniDir());
             PureIndex fst = PureIndex.openFst(miniDir())) {
            for (String q : QUERIES) {
                List<Result> a = trie.search(q, 10);
                List<Result> b = fst.search(q, 10);
                assertEquals("taille pour q=" + q, a.size(), b.size());
                for (int i = 0; i < a.size(); i++) {
                    Result ra = a.get(i), rb = b.get(i);
                    String ctx = "q=" + q + " rang " + i;
                    assertEquals(ctx + " voie", ra.voie(), rb.voie());
                    assertEquals(ctx + " cp", ra.cp(), rb.cp());
                    assertEquals(ctx + " ville", ra.ville(), rb.ville());
                    assertEquals(ctx + " score", ra.score(), rb.score(), 1e-9);
                }
            }
        }
    }
}
