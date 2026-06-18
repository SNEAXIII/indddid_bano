import csv
import os
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from utils.Perftime import perf_time


class RowMalformedError(Exception):
    """Exception levée lorsqu'une ligne du fichier CSV est malformée."""

    pass


class BANOParquetBuilder(ABC):
    """Classe abstraite pour les builders de fichiers Parquet BANO."""

    def __init__(self, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def reset_file(self):
        """Supprime le fichier Parquet existant."""
        if self.output_path.exists():
            print(f"Suppression du fichier existant: {self.output_path}")
            self.output_path.unlink()
            print("✓ Fichier supprimé")

    @staticmethod
    def add_error(errors, row, index, e=None):
        """Ajoute une erreur à la liste des erreurs d'import."""
        errors.append(row)

    @abstractmethod
    def _process_csv_row(self, row, index):
        """Traite une ligne du CSV et retourne un dictionnaire de données."""
        pass

    @abstractmethod
    def _get_schema(self):
        """Retourne le schéma PyArrow pour le fichier Parquet."""
        pass

    @perf_time
    def import_csv(
        self,
        csv_file_path,
        batch_size=50000,
        *,
        deduplicate: bool = False,
        print_duplicates: bool = True,
        max_print_duplicates: int = 50,
    ):
        """Importe un fichier CSV dans un fichier Parquet.

        Args:
            csv_file_path: Chemin du CSV.
            batch_size: Taille du batch écrit dans le parquet.
            deduplicate: Si True, ignore les lignes dont la clé (_dedup_key) a déjà été vue.
            print_duplicates: Si True, print les doublons détectés (jusqu'à max_print_duplicates).
            max_print_duplicates: Nombre max de doublons imprimés.
        """
        print(f"Import du fichier CSV: {csv_file_path}")
        if not Path(csv_file_path).exists():
            print(f"✗ Erreur: Le fichier {csv_file_path} n'existe pas")
            return

        count = 0
        errors = []
        batch_data = []

        # Déduplication streaming
        seen_keys = set() if deduplicate else None
        duplicates_count = 0
        duplicates_printed = 0

        try:
            with open(csv_file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",")
                writer = None

                for index, row in enumerate(reader):
                    try:
                        data = self._process_csv_row(row, index)
                        if not data:
                            continue

                        if seen_keys is not None:
                            key = (
                                (data.get("nom_voie") or "").strip(),
                                (data.get("code_postal") or "").strip(),
                                (data.get("nom_commune") or "").strip(),
                            )
                            if key in seen_keys:
                                duplicates_count += 1
                                if (
                                    print_duplicates
                                    and duplicates_printed < max_print_duplicates
                                ):
                                    print(
                                        "DUPLICATE (ignored) "
                                        f"at csv_index={index} key={key} data={data}"
                                    )
                                    duplicates_printed += 1
                                continue
                            seen_keys.add(key)

                        batch_data.append(data)
                        count += 1

                        if len(batch_data) >= batch_size:
                            if writer is None:
                                # Premier batch - créer le writer
                                df = pd.DataFrame(batch_data)
                                table = pa.Table.from_pandas(
                                    df, schema=self._get_schema()
                                )
                                writer = pq.ParquetWriter(
                                    str(self.output_path),
                                    schema=table.schema,
                                    compression="snappy",
                                )
                                writer.write_table(table)
                            else:
                                # Batchs suivants - ajouter au fichier
                                df = pd.DataFrame(batch_data)
                                table = pa.Table.from_pandas(
                                    df, schema=self._get_schema()
                                )
                                writer.write_table(table)

                            print(f"  {count} lignes importées...")
                            batch_data = []

                    except Exception as e:
                        self.add_error(errors, row, index, e)

                # Écrire les données restantes
                if batch_data:
                    df = pd.DataFrame(batch_data)
                    table = pa.Table.from_pandas(df, schema=self._get_schema())
                    if writer is None:
                        writer = pq.ParquetWriter(
                            str(self.output_path),
                            schema=table.schema,
                            compression="snappy",
                        )
                    writer.write_table(table)

                if writer:
                    writer.close()

                if seen_keys is not None:
                    print(
                        f"\n✓ Import terminé: {count} lignes importées, {len(errors)} erreurs, "
                        f"{duplicates_count} doublons ignorés"
                    )
                else:
                    print(
                        f"\n✓ Import terminé: {count} lignes importées, {len(errors)} erreurs"
                    )

        except Exception as e:
            print(f"✗ Erreur lors de l'import: {e}")
            raise

        # Afficher la taille du fichier
        if self.output_path.exists():
            size = os.path.getsize(self.output_path) / (1024 * 1024)  # En Mo
            print(f"Taille du fichier Parquet: {size:.2f} Mo")
            print("✓ Conversion terminée")

    def show_statistics(self):
        """Affiche les statistiques du fichier Parquet."""
        if not self.output_path.exists():
            print(f"✗ Erreur: Le fichier {self.output_path} n'existe pas")
            return

        print("\n" + "=" * 50)
        print("STATISTIQUES DU FICHIER PARQUET")
        print("=" * 50)

        # Lire les métadonnées
        parquet_file = pq.ParquetFile(str(self.output_path))
        print(f"Nombre de groupes de lignes: {parquet_file.num_row_groups}")
        print(f"Nombre total de lignes: {parquet_file.metadata.num_rows:,}")
        print(f"Nombre de colonnes: {parquet_file.metadata.num_columns}")

        print("\nSchéma:")
        print(parquet_file.schema)

        # Statistiques spécifiques
        self._display_statistics()

    @abstractmethod
    def _display_statistics(self):
        """Affiche les statistiques spécifiques."""
        pass

    def read_data(self):
        """Lit et retourne un DataFrame Pandas du fichier Parquet."""
        if not self.output_path.exists():
            print(f"✗ Erreur: Le fichier {self.output_path} n'existe pas")
            return None
        return pd.read_parquet(self.output_path)

    def query(self, filters=None, columns=None):
        """
        Effectue une requête sur le fichier Parquet.

        Args:
            filters: Liste de filtres PyArrow (ex: [('code_postal', '=', '75001')])
            columns: Liste des colonnes à retourner (None = toutes)
        """
        if not self.output_path.exists():
            print(f"✗ Erreur: Le fichier {self.output_path} n'existe pas")
            return None

        table = pq.read_table(str(self.output_path), filters=filters, columns=columns)
        return table.to_pandas()

    def auto_create(self, file_path: str):
        self.reset_file()
        self.import_csv(
            file_path,
            batch_size=100000,
            deduplicate=True,
            print_duplicates=True,
            max_print_duplicates=50,
        )
        self.show_statistics()
