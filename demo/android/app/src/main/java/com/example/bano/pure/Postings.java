package com.example.bano.pure;

import java.nio.ByteBuffer;

/** Lecteur postings.bin : tableau de u32 (rid) little-endian. */
public final class Postings {
    private final ByteBuffer buf;

    public Postings(ByteBuffer buf) {
        this.buf = buf;
    }

    /** rid à la position indexU32 (en unités u32 depuis le début). */
    public int rid(long indexU32) {
        return buf.getInt((int) (indexU32 * 4));
    }
}
