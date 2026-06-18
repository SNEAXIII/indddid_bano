package com.example.buildtools;

import org.apache.lucene.util.BytesRef;
import org.apache.lucene.util.IntsRefBuilder;
import org.apache.lucene.util.fst.Builder;
import org.apache.lucene.util.fst.FST;
import org.apache.lucene.util.fst.PositiveIntOutputs;
import org.apache.lucene.util.fst.Util;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Outil de build (hors APK) : prébuild le FST Lucene à partir de {@code vocab.bin}
 * et le sérialise en {@code lucene.fst}. Évite de reconstruire le FST en RAM à
 * chaque ouverture sur le device (le {@code FstMatcher} le charge directement).
 *
 * <p>Le format de {@code lucene.fst} est celui de Lucene (incompatible avec le
 * {@code index.fst} du Rust) — d'où ce prébuild côté JVM plutôt que côté Rust.</p>
 *
 * <p>vocab.bin (little-endian, écrit par Rust) : {@code u32 n | (n+1) u32 offsets |
 * n u64 packed | blob jetons}. Sortie FST = index vocab + 1 (PositiveIntOutputs
 * réserve 0 = NO_OUTPUT) — identique au {@code FstMatcher} embarqué.</p>
 */
public final class LuceneFstBuilder {
    private LuceneFstBuilder() {}

    public static void build(Path vocabBin, Path out) throws IOException {
        byte[] raw = Files.readAllBytes(vocabBin);
        ByteBuffer buf = ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);

        int n = buf.getInt(0);
        int offsetsStart = 4;
        int blobStart = offsetsStart + (n + 1) * 4 + n * 8; // après offsets + packed

        PositiveIntOutputs outputs = PositiveIntOutputs.getSingleton();
        Builder<Long> builder = new Builder<>(FST.INPUT_TYPE.BYTE1, outputs);
        IntsRefBuilder scratch = new IntsRefBuilder();

        int prev = buf.getInt(offsetsStart);
        for (int i = 0; i < n; i++) {
            int next = buf.getInt(offsetsStart + (i + 1) * 4);
            // Octets bruts du jeton (déjà triés en ordre croissant côté Rust).
            BytesRef key = new BytesRef(raw, blobStart + prev, next - prev);
            builder.add(Util.toIntsRef(key, scratch), (long) (i + 1));
            prev = next;
        }
        FST<Long> fst = builder.finish();

        Files.createDirectories(out.getParent());
        // save(Path) écrit meta + corps en séquence dans le même fichier
        // (relu côté device avec le même DataInput passé deux fois).
        fst.save(out);
        System.out.println("[LuceneFstBuilder] " + n + " jetons -> " + out
                + " (" + Files.size(out) + " octets)");
    }
}
