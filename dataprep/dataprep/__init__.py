"""Préparation des données BANO.

Télécharge l'export national `full.csv.gz`, le lit en streaming et en extrait
`streets.csv` : les triplets DISTINCTS `(voie, code_postal, ville)`.

Format de `full.csv` (sans en-tête, séparé par des virgules) :
    id, numero, voie, code_postal, ville, source, lat, lon
On ne garde que les colonnes 2, 3, 4 (indices Python), dédupliquées.
"""

from .pipeline import BANO_URL, prepare

__all__ = ["BANO_URL", "prepare"]
