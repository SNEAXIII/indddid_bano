package com.example.bano;

import android.content.Context;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/** Copie les fichiers d'index depuis assets/index/ vers filesDir/index/ (mmap exige un vrai fichier). */
public final class IndexAssets {
    private static final String[] INDEX_FILES =
            {"index.fst", "postings.bin", "records.bin", "vocab.bin"};

    private IndexAssets() {}

    public static File copyIfNeeded(Context ctx) throws Exception {
        File dir = new File(ctx.getFilesDir(), "index");
        if (!dir.exists()) {
            dir.mkdirs();
        }
        for (String name : INDEX_FILES) {
            File out = new File(dir, name);
            if (out.exists() && out.length() > 0) {
                continue;
            }
            try (InputStream in = ctx.getAssets().open("index/" + name);
                 OutputStream os = new FileOutputStream(out)) {
                byte[] buf = new byte[1 << 16];
                int n;
                while ((n = in.read(buf)) > 0) {
                    os.write(buf, 0, n);
                }
            }
        }
        return dir;
    }
}
