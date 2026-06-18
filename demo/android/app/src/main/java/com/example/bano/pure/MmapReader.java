package com.example.bano.pure;

import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.MappedByteBuffer;
import java.nio.channels.FileChannel;

/** Projette un fichier en mémoire (mmap), little-endian (comme l'écrit Rust). */
public final class MmapReader {
    private MmapReader() {}

    public static ByteBuffer map(String path) throws IOException {
        // Le mapping survit à la fermeture du canal (sémantique JVM).
        try (RandomAccessFile raf = new RandomAccessFile(path, "r");
             FileChannel ch = raf.getChannel()) {
            MappedByteBuffer mbb = ch.map(FileChannel.MapMode.READ_ONLY, 0, ch.size());
            mbb.order(ByteOrder.LITTLE_ENDIAN);
            return mbb;
        }
    }
}
