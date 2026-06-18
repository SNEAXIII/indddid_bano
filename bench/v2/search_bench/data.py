# search_bench/data.py
"""Chargement des triplets BANO depuis streets.csv."""

import csv
from dataclasses import dataclass

from search_bench.normalize import normalize, tokenize


@dataclass(frozen=True)
class Record:
    voie: str
    code_postal: str
    ville: str

    def __post_init__(self) -> None:
        joined = f"{self.voie} {self.code_postal} {self.ville}"
        object.__setattr__(self, "search_text", normalize(joined))
        object.__setattr__(self, "tokens", tokenize(joined))


def load_records(csv_path: str, limit: int | None = None) -> list[Record]:
    """Charge streets.csv. Ignore les lignes sans voie/ville (malformées).

    `limit` : ne garde que les `limit` premières lignes valides (None = tout).
    Déterministe (mêmes N lignes du même fichier) -> sous-ensemble cohérent
    entre generate / prebuild / bench.
    """
    records: list[Record] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            voie = (row.get("voie") or "").strip()
            cp = (row.get("code_postal") or "").strip()
            ville = (row.get("ville") or "").strip()
            if not voie or not ville:
                continue
            records.append(Record(voie=voie, code_postal=cp, ville=ville))
            if limit is not None and len(records) >= limit:
                break
    return records
