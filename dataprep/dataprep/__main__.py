"""Point d'entrée CLI : `python -m dataprep --out <chemin streets.csv>`."""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import BANO_URL, prepare

# Racine du dépôt = dataprep/../  -> data/streets.csv par défaut.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_OUT = _REPO_ROOT / "data" / "streets.csv"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dataprep",
        description="Télécharge le BANO full et en extrait streets.csv.",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=_DEFAULT_OUT,
        help=f"chemin de sortie streets.csv (défaut : {_DEFAULT_OUT})",
    )
    parser.add_argument(
        "--gz",
        type=Path,
        default=None,
        help="cache du .gz (défaut : <out.parent>/full.csv.gz)",
    )
    parser.add_argument("--url", default=BANO_URL, help="URL de l'archive BANO full")
    parser.add_argument(
        "-f", "--force", action="store_true", help="régénère même si streets.csv existe"
    )
    args = parser.parse_args()

    # Chemins relatifs : ancrés sur la racine du dépôt (jamais sur le cwd),
    # pour que `streets.csv` finisse toujours dans data/ même si on lance
    # depuis dataprep/. Un chemin absolu est respecté tel quel.
    def _anchor(p: Path | None) -> Path | None:
        if p is None:
            return None
        return p if p.is_absolute() else _REPO_ROOT / p

    out = _anchor(args.out)
    gz = _anchor(args.gz)

    prepare(out, url=args.url, gz=gz, force=args.force)


if __name__ == "__main__":
    main()
