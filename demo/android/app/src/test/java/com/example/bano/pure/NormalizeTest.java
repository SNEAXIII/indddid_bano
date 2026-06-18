package com.example.bano.pure;

import static org.junit.Assert.assertEquals;

import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class NormalizeTest {
    @Test public void apostropheEtAccent() {
        assertEquals("rue de l egalite", Normalize.normalize("Rue de l'Égalité"));
    }
    @Test public void tiretEtAccent() {
        assertEquals("saint etienne", Normalize.normalize("Saint-Étienne"));
    }
    @Test public void majuscules() {
        assertEquals("paris", Normalize.normalize("PARIS"));
    }
    @Test public void espacesMultiples() {
        assertEquals("bourg en bresse", Normalize.normalize("  Bourg   en  Bresse  "));
    }
    @Test public void tokenisation() {
        assertEquals(Arrays.asList("bourg", "en", "bresse"),
                Normalize.tokenize("Bourg-en-Bresse"));
    }
    @Test public void tokeniseVide() {
        List<String> t = Normalize.tokenize("   ");
        assertEquals(0, t.size());
    }
}
