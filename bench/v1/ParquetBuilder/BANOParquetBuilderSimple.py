import pandas as pd
import pyarrow as pa

from ParquetBuilder.Interface.BANOParquetBuilder import (
    BANOParquetBuilder,
    RowMalformedError,
)


class BANOParquetBuilderSimple(BANOParquetBuilder):
    """Builder pour un fichier Parquet BANO simple avec les 3 colonnes principales."""

    def __init__(self, output_path="bano_data.parquet"):
        super().__init__(output_path)

    def _get_schema(self):
        """Retourne le schéma PyArrow pour le fichier Parquet."""
        return pa.schema(
            [
                ("nom_voie", pa.string()),
                ("code_postal", pa.string()),
                ("nom_commune", pa.string()),
            ]
        )

    def _process_csv_row(self, row, index):
        """Traite une ligne du CSV pour créer un dictionnaire de données."""
        if len(row) < 3:
            raise RowMalformedError("Ligne avec moins de 3 colonnes")

        # Extraction des 3 champs principaux
        nom_voie = row[0].strip()
        code_postal = row[1].strip()
        nom_commune = row[2].strip()

        # Validation
        if not code_postal or not nom_commune or not nom_voie:
            raise RowMalformedError("Champs vides détectés")

        return {
            "nom_voie": nom_voie,
            "code_postal": code_postal,
            "nom_commune": nom_commune,
        }

    def _display_statistics(self):
        """Affiche les statistiques spécifiques."""
        df = pd.read_parquet(self.output_path)

        print(f"\nNombre total d'adresses: {len(df):,}")
        print(f"Voies distinctes: {df['nom_voie'].nunique():,}")
        print(f"Codes postaux distincts: {df['code_postal'].nunique():,}")
        print(f"Communes distinctes: {df['nom_commune'].nunique():,}")

    def _display_sample_data(self):
        """Affiche des exemples de données."""
        df = pd.read_parquet(self.output_path)
        print("\nExemples d'adresses (10 premières):")
        for _, row in df.head(10).iterrows():
            print(
                f"  - {row['nom_voie']} | {row['code_postal']} | {row['nom_commune']}"
            )


if __name__ == "__main__":
    builder = BANOParquetBuilderSimple("bano_simple.parquet")
    builder.auto_create("streets.csv")
