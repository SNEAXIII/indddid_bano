package com.example.bano.pure;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

/** Lecteur vocab.bin : u32 n | (n+1) u32 offsets | n u64 packed | blob jetons. */
public final class Vocab {
    private final ByteBuffer buf;
    private final int n;
    private static final int OFFSETS_START = 4;
    private final int packedStart;
    private final int blobStart;

    public Vocab(ByteBuffer buf) {
        this.buf = buf;
        this.n = buf.getInt(0);
        this.packedStart = OFFSETS_START + (n + 1) * 4;
        this.blobStart = packedStart + n * 8;
    }

    public int size() {
        return n;
    }

    /** packed = (offset_postings << 32) | len. */
    public long packed(int i) {
        return buf.getLong(packedStart + i * 8);
    }

    public String token(int i) {
        int off = buf.getInt(OFFSETS_START + i * 4);
        int offNext = buf.getInt(OFFSETS_START + (i + 1) * 4);
        byte[] bytes = new byte[offNext - off];
        for (int k = 0; k < bytes.length; k++) {
            bytes[k] = buf.get(blobStart + off + k);
        }
        return new String(bytes, StandardCharsets.UTF_8);
    }

    /** Décode tous les jetons en une passe (lecture bulk du blob, pas octet par octet). */
    public String[] allTokens() {
        int blobLen = buf.getInt(OFFSETS_START + n * 4);
        byte[] blob = new byte[blobLen];
        ByteBuffer d = buf.duplicate();
        d.position(blobStart);
        d.get(blob);
        String[] out = new String[n];
        int prev = buf.getInt(OFFSETS_START);
        for (int i = 0; i < n; i++) {
            int next = buf.getInt(OFFSETS_START + (i + 1) * 4);
            out[i] = new String(blob, prev, next - prev, StandardCharsets.UTF_8);
            prev = next;
        }
        return out;
    }
}
