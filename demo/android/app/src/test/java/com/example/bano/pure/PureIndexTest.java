package com.example.bano.pure;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import com.example.bano.Result;
import java.io.File;
import java.util.List;
import org.junit.Test;

public class PureIndexTest {
    private String miniDir() {
        return new File("src/test/resources/mini").getAbsolutePath();
    }

    @Test public void villeExacteDeuxResultats() throws Exception {
        try (PureIndex idx = PureIndex.open(miniDir())) {
            List<Result> hits = idx.search("paris", 10);
            assertEquals(2, hits.size());
            assertEquals("75002", hits.get(0).cp());
            assertEquals("75016", hits.get(1).cp());
        }
    }

    @Test public void intersectionEtDeuxJetons() throws Exception {
        try (PureIndex idx = PureIndex.open(miniDir())) {
            List<Result> hits = idx.search("rue paix", 10);
            assertFalse(hits.isEmpty());
            assertEquals("Rue de la Paix", hits.get(0).voie());
        }
    }

    @Test public void typoToleree() throws Exception {
        try (PureIndex idx = PureIndex.open(miniDir())) {
            List<Result> hits = idx.search("pari", 10);
            assertTrue(hits.stream().anyMatch(r -> r.ville().equals("Paris")));
        }
    }

    @Test public void requeteVide() throws Exception {
        try (PureIndex idx = PureIndex.open(miniDir())) {
            assertEquals(0, idx.search("   ", 10).size());
        }
    }
}
