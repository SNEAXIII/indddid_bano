"""Cœur de la préparation : download + extraction de streets.csv."""

from __future__ import annotations

import csv
import gzip
import sys
import urllib.request
from pathlib import Path

BANO_URL = "https://bano.openstreetmap.fr/data/full.csv.gz"

# Indices des colonnes utiles dans full.csv (id,numero,VOIE,CP,VILLE,source,lat,lon).
_COL_VOIE, _COL_CP, _COL_VILLE = 2, 3, 4
_MIN_COLS = 5


def _download(url: str, dest: Path) -> None:
    """Télécharge `url` vers `dest` (via un .part renommé à la fin)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    print(f"[dataprep] téléchargement {url}", file=sys.stderr)

    def _progress(blocks: int, block_size: int, total: int) -> None:
        if total > 0:
            done = min(blocks * block_size, total)
            pct = 100 * done / total
            print(
                f"\r[dataprep]   {done / 1e6:7.1f} / {total / 1e6:.1f} Mo "
                f"({pct:5.1f} %)",
                end="",
                file=sys.stderr,
            )

    urllib.request.urlretrieve(url, part, _progress)  # noqa: S310 (URL fixe, HTTPS)
    print(file=sys.stderr)
    part.replace(dest)


def _extract_streets(gz_path: Path, out_path: Path) -> int:
    """Lit `gz_path` en streaming, écrit les triplets distincts dans `out_path`.

    Retourne le nombre de voies uniques écrites.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, str, str]] = set()
    tmp = out_path.with_suffix(out_path.suffix + ".part")

    with (
        gzip.open(gz_path, mode="rt", encoding="utf-8", newline="") as gz,
        open(tmp, "w", encoding="utf-8", newline="") as out,
    ):
        reader = csv.reader(gz)
        writer = csv.writer(out)
        writer.writerow(["voie", "code_postal", "ville"])
        for row in reader:
            if len(row) < _MIN_COLS:
                continue
            voie = row[_COL_VOIE].strip()
            cp = row[_COL_CP].replace(",", "").strip()
            ville = row[_COL_VILLE].strip()
            if not voie or not ville:
                continue
            key = (voie, cp, ville)
            if key in seen:
                continue
            seen.add(key)
            writer.writerow(key)

    tmp.replace(out_path)
    return len(seen)


def prepare(
    out: Path, *, url: str = BANO_URL, gz: Path | None = None, force: bool = False
) -> Path:
    """S'assure que `out` (streets.csv) existe ; le génère sinon.

    - `out`   : chemin de sortie streets.csv.
    - `gz`    : cache du .gz téléchargé (défaut : `<out.parent>/full.csv.gz`).
    - `force` : régénère même si `out` existe déjà.
    """
    out = Path(out)
    gz = Path(gz) if gz is not None else out.parent / "full.csv.gz"

    if out.exists() and not force:
        print(f"[dataprep] {out} déjà présent — rien à faire.", file=sys.stderr)
        return out

    if not gz.exists():
        _download(url, gz)
    else:
        print(f"[dataprep] archive présente : {gz}", file=sys.stderr)

    print(f"[dataprep] extraction des voies uniques -> {out}", file=sys.stderr)
    n = _extract_streets(gz, out)
    print(
        f"[dataprep] {n:,} voies uniques écrites dans {out}".replace(",", " "),
        file=sys.stderr,
    )
    return out
