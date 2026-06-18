package com.example.bano.pure;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public class IntFloatMapTest {

    @Test public void putGetEtDefaut() {
        IntFloatMap m = new IntFloatMap(4);
        m.put(42, 1.5f);
        assertEquals(1.5f, m.get(42, 0f), 0f);
        assertEquals(-1f, m.get(7, -1f), 0f);
        assertEquals(1, m.size());
    }

    @Test public void maxPutGardeLeMax() {
        IntFloatMap m = new IntFloatMap(4);
        m.maxPut(1, 0.5f);
        m.maxPut(1, 0.9f);
        m.maxPut(1, 0.3f);
        assertEquals(0.9f, m.get(1, 0f), 0f);
        assertEquals(1, m.size());
    }

    @Test public void croissanceConserveLesEntrees() {
        IntFloatMap m = new IntFloatMap(4);
        for (int i = 0; i < 10_000; i++) m.put(i, i * 0.5f);
        assertEquals(10_000, m.size());
        for (int i = 0; i < 10_000; i++) {
            assertEquals(i * 0.5f, m.get(i, Float.NaN), 0f);
        }
    }

    @Test public void iterationBrute() {
        IntFloatMap m = new IntFloatMap(4);
        m.put(3, 1f);
        m.put(9, 2f);
        int[] keys = m.keysRaw();
        float[] vals = m.valsRaw();
        float sum = 0;
        for (int i = 0; i < keys.length; i++) {
            if (keys[i] != IntFloatMap.EMPTY) sum += vals[i];
        }
        assertEquals(3f, sum, 0f);
    }
}
