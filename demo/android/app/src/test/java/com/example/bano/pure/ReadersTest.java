package com.example.bano.pure;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.ByteBuffer;
import org.junit.Test;

public class ReadersTest {
    private String mini(String name) {
        return new File("src/test/resources/mini/" + name).getAbsolutePath();
    }

    @Test public void vocabTriEtTaille() throws Exception {
        ByteBuffer vb = MmapReader.map(mini("vocab.bin"));
        Vocab vocab = new Vocab(vb);
        assertTrue("vocab non vide", vocab.size() > 0);
        for (int i = 0; i + 1 < vocab.size(); i++) {
            assertTrue("jetons tries", vocab.token(i).compareTo(vocab.token(i + 1)) <= 0);
        }
        boolean foundParis = false;
        for (int i = 0; i < vocab.size(); i++) {
            if (vocab.token(i).equals("paris")) {
                foundParis = true;
                long packed = vocab.packed(i);
                long len = packed & 0xFFFFFFFFL;
                assertEquals(2, len);
            }
        }
        assertTrue("paris dans le vocab", foundParis);
    }

    @Test public void postingsEtRecords() throws Exception {
        ByteBuffer vb = MmapReader.map(mini("vocab.bin"));
        ByteBuffer pb = MmapReader.map(mini("postings.bin"));
        ByteBuffer rb = MmapReader.map(mini("records.bin"));
        Vocab vocab = new Vocab(vb);
        Postings postings = new Postings(pb);
        Records records = new Records(rb);

        assertEquals(3, records.size());

        for (int i = 0; i < vocab.size(); i++) {
            if (!vocab.token(i).equals("paris")) continue;
            long packed = vocab.packed(i);
            long off = packed >>> 32;
            long len = packed & 0xFFFFFFFFL;
            for (long k = 0; k < len; k++) {
                int rid = postings.rid(off + k);
                String[] rec = records.record(rid);
                assertEquals("Paris", rec[2]);
            }
        }
    }
}
