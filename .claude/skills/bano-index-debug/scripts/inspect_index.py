#!/usr/bin/env python3
"""Inspecteur des artefacts binaires de l'index BANO (vocab/postings/records).

L'index FST (`index.fst`) est opaque en Python (format du crate `fst`), MAIS
`vocab.bin` contient EXACTEMENT les mêmes jetons + valeurs `packed` que le FST
(garanti par build.rs : test `vocab_bin_matches_fst`). On inspecte donc
`vocab.bin` comme miroir lisible du FST — c'est aussi le fichier que lit le
moteur Java (PureIndex). Décoder ça à la main est le meilleur moyen de voir ce
que la recherche voit vraiment, sans dépendre des traces.

Formats (tout en little-endian) :
  vocab.bin    : u32 n | (n+1) u32 offsets | n u64 packed | blob jetons UTF-8 (TRIÉ)
  postings.bin : suite de u32 (les rid)
  records.bin  : u32 n | (n+1) u32 offsets | blob ; champs séparés par 0x01
  packed (u64) : (offset_postings_en_u32 << 32) | nb_rid

Usage :
  python inspect_index.py <dir> stats
  python inspect_index.py <dir> token <jeton> [n]    # postings d'un jeton + n records résolus (défaut 30)
  python inspect_index.py <dir> grep <sous-chaine>   # jetons contenant la sous-chaine
  python inspect_index.py <dir> record <rid>         # un enregistrement par son id
  python inspect_index.py <dir> check                # cohérence vocab/postings/records
"""

import struct
import sys


def _read(path):
    with open(path, "rb") as f:
        return f.read()


class Vocab:
    def __init__(self, dir_):
        b = _read(f"{dir_}/vocab.bin")
        self.raw = b
        (n,) = struct.unpack_from("<I", b, 0)
        self.n = n
        off_start = 4
        self.offsets = struct.unpack_from(f"<{n + 1}I", b, off_start)
        packed_start = off_start + (n + 1) * 4
        self.packed = struct.unpack_from(f"<{n}Q", b, packed_start)
        self.blob_start = packed_start + n * 8

    def token(self, i):
        o, o2 = self.offsets[i], self.offsets[i + 1]
        return self.raw[self.blob_start + o : self.blob_start + o2].decode("utf-8")

    def all_tokens(self):
        return [self.token(i) for i in range(self.n)]

    def find(self, tok):
        """Recherche binaire (le vocab est trié par octets, comme le FST)."""
        target = tok.encode("utf-8")
        lo, hi = 0, self.n
        while lo < hi:
            mid = (lo + hi) // 2
            o, o2 = self.offsets[mid], self.offsets[mid + 1]
            cur = self.raw[self.blob_start + o : self.blob_start + o2]
            if cur < target:
                lo = mid + 1
            elif cur > target:
                hi = mid
            else:
                return mid
        return -1

    def unpack(self, i):
        p = self.packed[i]
        return p >> 32, p & 0xFFFFFFFF  # (offset en u32, len)


class Postings:
    def __init__(self, dir_):
        self.raw = _read(f"{dir_}/postings.bin")
        self.count = len(self.raw) // 4

    def rids(self, off_u32, length):
        return list(struct.unpack_from(f"<{length}I", self.raw, off_u32 * 4))


class Records:
    def __init__(self, dir_):
        b = _read(f"{dir_}/records.bin")
        self.raw = b
        (n,) = struct.unpack_from("<I", b, 0)
        self.n = n
        self.offsets = struct.unpack_from(f"<{n + 1}I", b, 4)
        self.blob_start = 4 + (n + 1) * 4

    def record(self, rid):
        o, o2 = self.offsets[rid], self.offsets[rid + 1]
        text = self.raw[self.blob_start + o : self.blob_start + o2].decode("utf-8")
        parts = text.split("\x01")
        while len(parts) < 3:
            parts.append("")
        return parts[0], parts[1], parts[2]


def cmd_stats(dir_):
    v, p, r = Vocab(dir_), Postings(dir_), Records(dir_)
    print(f"dir            : {dir_}")
    print(f"records        : {r.n}")
    print(f"jetons (vocab) : {v.n}")
    print(f"postings (u32) : {p.count}")
    total = sum(v.unpack(i)[1] for i in range(v.n))
    print(
        f"somme len      : {total}  (doit == postings: {'OK' if total == p.count else 'MISMATCH'})"
    )
    longest = max(range(v.n), key=lambda i: v.unpack(i)[1])
    off, ln = v.unpack(longest)
    print(f"jeton + frequent: {v.token(longest)!r} -> {ln} records")


def cmd_token(dir_, tok, show=30):
    v, p, r = Vocab(dir_), Postings(dir_), Records(dir_)
    i = v.find(tok)
    if i < 0:
        print(f"jeton {tok!r} ABSENT du vocab (recherche exacte). Essaie: grep")
        return
    off, ln = v.unpack(i)
    rids = p.rids(off, ln)
    print(f"jeton {tok!r}  index={i}  offset_postings={off}  len={ln}")
    head = rids if len(rids) <= 50 else rids[:50]
    print(f"rids ({len(rids)}){' ' if len(rids) <= 50 else ' [50 premiers] '}: {head}")
    for rid in rids[:show]:
        voie, cp, ville = r.record(rid)
        print(f"  [{rid}] {voie} | {cp} | {ville}")
    if len(rids) > show:
        print(f"  ... ({len(rids) - show} records de plus ; arg final = nb à résoudre)")


def cmd_grep(dir_, sub):
    v = Vocab(dir_)
    hits = [(i, v.token(i)) for i in range(v.n) if sub in v.token(i)]
    print(f"{len(hits)} jeton(s) contenant {sub!r} :")
    for i, t in hits[:200]:
        _, ln = v.unpack(i)
        print(f"  {t!r} -> {ln} records")
    if len(hits) > 200:
        print(f"  ... ({len(hits) - 200} de plus)")


def cmd_record(dir_, rid):
    r = Records(dir_)
    rid = int(rid)
    if rid < 0 or rid >= r.n:
        print(f"rid {rid} hors bornes (0..{r.n - 1})")
        return
    voie, cp, ville = r.record(rid)
    print(f"[{rid}] voie={voie!r} cp={cp!r} ville={ville!r}")


def cmd_check(dir_):
    v, p, r = Vocab(dir_), Postings(dir_), Records(dir_)
    problems = []
    # vocab trié ?
    toks = v.all_tokens()
    if toks != sorted(toks, key=lambda s: s.encode("utf-8")):
        problems.append("vocab NON trié par octets (le FST exige l'ordre croissant)")
    # somme des len == nb postings ?
    total = sum(v.unpack(i)[1] for i in range(v.n))
    if total != p.count:
        problems.append(f"somme len ({total}) != postings ({p.count})")
    # tous les rid valides ?
    bad = 0
    for i in range(v.n):
        off, ln = v.unpack(i)
        for rid in p.rids(off, ln):
            if rid >= r.n:
                bad += 1
    if bad:
        problems.append(f"{bad} rid hors bornes (>= {r.n})")
    if problems:
        print("PROBLEMES :")
        for x in problems:
            print(f"  - {x}")
        sys.exit(1)
    print(f"OK : {v.n} jetons, {p.count} postings, {r.n} records, tout cohérent.")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    dir_, cmd = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    table = {
        "stats": lambda: cmd_stats(dir_),
        "token": lambda: cmd_token(
            dir_, args[0], int(args[1]) if len(args) > 1 else 30
        ),
        "grep": lambda: cmd_grep(dir_, args[0]),
        "record": lambda: cmd_record(dir_, args[0]),
        "check": lambda: cmd_check(dir_),
    }
    if cmd not in table:
        print(f"commande inconnue: {cmd}\n{__doc__}")
        sys.exit(2)
    table[cmd]()


if __name__ == "__main__":
    main()
