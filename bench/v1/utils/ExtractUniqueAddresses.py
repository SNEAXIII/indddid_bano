#!/usr/bin/env python3
"""
Script pour extraire les voies, codes postaux et villes uniques d'un fichier BANO CSV.
Génère un nouveau fichier CSV avec ces informations.
"""

import argparse
import csv
from pathlib import Path


def extract_unique_addresses(input_file: str, output_file: str) -> None:
    """
    Extrait les voies, codes postaux et villes uniques d'un fichier BANO CSV.

    Args:
        input_file: Chemin du fichier CSV d'entrée
        output_file: Chemin du fichier CSV de sortie
    """
    streets_set = set()

    print(f"Début de la lecture du fichier: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        row_count = 0

        for row in reader:
            row_count += 1

            if row_count % 100_000 == 0:
                print(f"Traitement de la ligne {row_count:,}...")

            if len(row) >= 5:
                # Colonnes: id, numero, voie, code_postal, ville, source, lat, lon
                voie = row[2].strip()
                code_postal = row[3].replace(",", "").strip()
                ville = row[4].strip()
                streets_set.add((voie, code_postal, ville))

    print(f"\nLecture terminée. {row_count:,} lignes lues.")
    print(f"Nombre de voies uniques trouvées: {len(streets_set):,}")

    # Trier par code postal, puis ville, puis voie
    print("Tri des données...")
    sorted_streets = sorted(streets_set, key=lambda x: (x[1], x[2], x[0]))

    # Écrire le fichier de sortie
    print(f"Écriture du fichier de sortie: {output_file}")
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["voie", "code_postal", "ville"])
        writer.writerows(sorted_streets)

    print("\nExtraction terminée !")
    print(f"  - Fichier source: {input_file}")
    print(f"  - Fichier de sortie: {output_file}")
    print(f"  - Nombre de voies uniques: {len(sorted_streets):,}")


def main():
    parser = argparse.ArgumentParser(
        description="Extrait les voies, codes postaux et villes d'un fichier BANO CSV."
    )
    parser.add_argument(
        "-i",
        "--input",
        default="full.csv",
        help="Fichier CSV d'entrée (défaut: full.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="streets.csv",
        help="Fichier CSV de sortie (défaut: streets.csv)",
    )

    args = parser.parse_args()

    # Vérifier que le fichier d'entrée existe
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Erreur: Le fichier '{args.input}' n'existe pas.")

    extract_unique_addresses(args.input, args.output)


if __name__ == "__main__":
    main()
