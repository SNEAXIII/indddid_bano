package com.example.bano.bench;

import static org.junit.Assert.assertEquals;

import com.example.bano.Result;
import java.util.Arrays;
import java.util.List;
import org.junit.Test;

public class BenchMetricsTest {
    @Test public void percentileInterpole() {
        List<Double> v = Arrays.asList(1.0, 2.0, 3.0, 4.0);
        assertEquals(2.5, BenchMetrics.percentile(v, 50), 1e-9);
        assertEquals(1.0, BenchMetrics.percentile(v, 0), 1e-9);
        assertEquals(4.0, BenchMetrics.percentile(v, 100), 1e-9);
    }

    @Test public void recallEtMrr() {
        Result hit = new Result(1.0, "Rue de la Paix", "75002", "Paris");
        Result other = new Result(0.5, "X", "00000", "Y");
        List<Result> results = Arrays.asList(other, hit);
        assertEquals(1.0, BenchMetrics.recallAtK(results, "Rue de la Paix", "75002", "Paris", 5), 1e-9);
        assertEquals(0.0, BenchMetrics.recallAtK(results, "Rue de la Paix", "75002", "Paris", 1), 1e-9);
        assertEquals(0.5, BenchMetrics.reciprocalRank(results, "Rue de la Paix", "75002", "Paris"), 1e-9);
    }

    @Test public void wordCountCompteLesMots() {
        assertEquals(0, BenchMetrics.wordCount(""));
        assertEquals(0, BenchMetrics.wordCount("   "));
        assertEquals(0, BenchMetrics.wordCount(null));
        assertEquals(1, BenchMetrics.wordCount("villevijeanne"));
        assertEquals(2, BenchMetrics.wordCount("villevijeanne 231"));
        assertEquals(3, BenchMetrics.wordCount("lupersat 23190 villevijeanne"));
        assertEquals(3, BenchMetrics.wordCount("  lupersat   23190 \t villevijeanne  "));
    }
}
