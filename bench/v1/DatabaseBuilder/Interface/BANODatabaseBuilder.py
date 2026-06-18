import csv
import os

from abc import ABC, abstractmethod
from pathlib import Path

from utils.DatabaseCursor import DatabaseCursor
from utils.Perftime import perf_time


class RowMalformedError(Exception):
    """Exception levée lorsqu'une ligne du fichier CSV est malformée."""

    pass


class BANODatabaseBuilder(ABC):
    """Classe abstraite pour les builders de base de données BANO."""

    def __init__(self, cursor: DatabaseCursor, tables: dict[str, str]):
        self.tables = tables
        self.cursor = cursor
        self.db_path = cursor.db_path

    def reset_db(self):
        """Supprime et recrée les tables de la base de données."""
        self.delete_tables()
        self.create_tables()

    def create_tables(self):
        print("Création des tables...")
        for table, table_content in self.tables.items():
            print(f"  Création de la table {table}...")
            self.cursor.execute(table_content)
        print("✓ Tables créées")
        self.cursor.commit()
        self.cursor.vacuum()

    def delete_tables(self):
        """Supprime complètement toutes les tables de la base de données."""
        print("Suppression des tables...")
        # Utilise get_table_names() pour avoir une liste blanche sécurisée
        for table in self.tables.keys():
            # table vient de get_table_names(), donc c'est sûr
            query = f"DROP TABLE IF EXISTS {table}"
            print(f"  Suppression de la table '{table}'...")
            self.cursor.execute(query)
        self.cursor.commit()
        self.cursor.vacuum()
        print("✓ Tables supprimées et base optimisée")

    @staticmethod
    def add_error(errors, row, index, e=None):
        """Ajoute une erreur à la liste des erreurs d'import."""
        # print(f"Erreur ligne {index}: {row}")
        # if e:
        #     print(f"  Détail de l'erreur: {e}")
        errors.append(row)

    @perf_time
    def import_csv(self, csv_file_path, batch_size=50000):
        """Importe un fichier CSV dans la base de données."""
        print(f"Import du fichier CSV: {csv_file_path}")
        if not Path(csv_file_path).exists():
            print(f"✗ Erreur: Le fichier {csv_file_path} n'existe pas")
            return
        count = 0
        errors = []
        try:
            with open(csv_file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",")
                for index, row in enumerate(reader):
                    try:
                        count += self._process_csv_row(row, index)
                        if count % batch_size == 0:
                            self.cursor.commit()
                            print(f"  {count} lignes importées...")
                    except Exception as e:
                        self.add_error(errors, row, index, e)
                self.cursor.commit()
                print(
                    f"\n✓ Import terminé: {count} lignes importées, {len(errors)} erreurs"
                )
        except Exception as e:
            print(f"✗ Erreur lors de l'import: {e}")
            self.cursor.rollback()

        size_before = os.path.getsize(self.db_path) / (1024 * 1024)  # En Mo
        print(f"Taille avant optimisation: {size_before:.2f} Mo")
        # VACUUM compresse la base et libère l'espace inutilisé
        self.cursor.vacuum()
        # ANALYZE met à jour les statistiques pour améliorer les performances des requêtes
        self.cursor.execute("ANALYZE")
        self.cursor.commit()
        # Récupérer la taille après optimisation
        size_after = os.path.getsize(self.db_path) / (1024 * 1024)  # En Mo
        saved = size_before - size_after
        percent = (saved / size_before * 100) if size_before > 0 else 0
        print(f"Taille après optimisation: {size_after:.2f} Mo")
        print(f"Espace économisé: {saved:.2f} Mo ({percent:.1f}%)")
        print("✓ Optimisation terminée")

    @abstractmethod
    def _process_csv_row(self, row, index):
        """Traite une ligne du CSV. Retourne 1 si succès, 0 sinon."""
        pass

    @abstractmethod
    def _display_statistics(self):
        """Affiche les statistiques spécifiques."""
        pass

    def show_statistics(self):
        """Affiche les statistiques de la base de données."""
        slicer_equal = "=" * 60
        print("\n" + slicer_equal)
        print("STATISTIQUES DE LA BASE DE DONNÉES")
        print(slicer_equal)
        self._display_statistics()

    def auto_create(self, file_path: str):
        self.reset_db()
        self.import_csv(file_path, batch_size=100000)
        self.show_statistics()
