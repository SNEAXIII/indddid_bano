# search_bench/engines/base.py
"""Interface commune à toutes les méthodes de recherche."""

import os
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass

from search_bench.data import Record
from search_bench.engines._artifact import dir_size_bytes, read_meta, write_meta


@dataclass
class Result:
    voie: str
    code_postal: str
    ville: str
    score: float


class SearchEngine(ABC):
    #: nom court de la méthode (clé du rapport)
    name: str = "base"
    #: True si la méthode tolère les fautes de frappe
    supports_fuzzy: bool = False
    #: temps de construction de l'index, rempli par build()
    build_time_ms: float = 0.0
    #: taille de l'artefact sur disque (octets), -1 si purement en mémoire
    artifact_size_bytes: int = -1

    @abstractmethod
    def build(self, records: list[Record]) -> None:
        """Construit l'index/artefact à partir des records."""

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[Result]:
        """Retourne au plus `limit` résultats triés par score décroissant."""

    def close(self) -> None:
        """Libère les ressources (connexions, fichiers). No-op par défaut."""

    def save(self, artifact_dir: str) -> None:
        """Persiste le moteur. Défaut : pickle de l'instance + meta.json.

        Convient aux moteurs purement en mémoire. Les moteurs à ressources
        externes (connexion SQLite, fichier colonnaire) surchargent cette méthode.
        """
        os.makedirs(artifact_dir, exist_ok=True)
        with open(os.path.join(artifact_dir, "engine.pkl"), "wb") as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
        size = dir_size_bytes(artifact_dir)
        if self.artifact_size_bytes < 0:
            self.artifact_size_bytes = size
        write_meta(artifact_dir, self.build_time_ms, self.artifact_size_bytes)

    @classmethod
    def load(cls, artifact_dir: str) -> "SearchEngine":
        """Recharge le moteur. Défaut : unpickle + meta.json."""
        with open(os.path.join(artifact_dir, "engine.pkl"), "rb") as f:
            engine = pickle.load(f)
        meta = read_meta(artifact_dir)
        engine.build_time_ms = meta["build_time_ms"]
        engine.artifact_size_bytes = meta["artifact_size_bytes"]
        return engine
