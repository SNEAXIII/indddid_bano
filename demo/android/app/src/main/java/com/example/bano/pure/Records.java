package com.example.bano.pure;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

/** Lecteur records.bin : u32 n | (n+1) u32 offsets | blob UTF-8 (sep 0x01). */
public final class Records {
    private final ByteBuffer buf;
    private final int n;
    private static final int OFFSETS_START = 4;
    private final int blobStart;
    /** SOH / 0x01 separator used by the Rust encoder. */
    private static final String SEP = String.valueOf((char) 1);

    public Records(ByteBuffer buf) {
        this.buf = buf;
        this.n = buf.getInt(0);
        this.blobStart = OFFSETS_START + (n + 1) * 4;
    }

    public int size() {
        return n;
    }

    /** Renvoie [voie, cp, ville] pour le record rid. */
    public String[] record(int rid) {
        int off = buf.getInt(OFFSETS_START + rid * 4);
        int offNext = buf.getInt(OFFSETS_START + (rid + 1) * 4);
        byte[] bytes = new byte[offNext - off];
        for (int k = 0; k < bytes.length; k++) {
            bytes[k] = buf.get(blobStart + off + k);
        }
        String text = new String(bytes, StandardCharsets.UTF_8);
        String[] parts = text.split(SEP, -1);
        String voie = parts.length > 0 ? parts[0] : "";
        String cp = parts.length > 1 ? parts[1] : "";
        String ville = parts.length > 2 ? parts[2] : "";
        return new String[] {voie, cp, ville};
    }
}
