from utils.DatabaseCursor import DatabaseCursor
from DatabaseBuilder.Interface.BANODatabaseBuilder import (
    BANODatabaseBuilder,
    RowMalformedError,
)


class BANODatabaseBuilderNoJoinsWoRowid(BANODatabaseBuilder):
    """Builder pour une base BANO avec une seule table sans jointures."""

    def __init__(self, cursor: DatabaseCursor):
        tables = {
            "adresses": """
                CREATE TABLE IF NOT EXISTS adresses (
                    nom_voie TEXT NOT NULL,
                    code_postal TEXT NOT NULL,
                    nom_commune TEXT NOT NULL,
                    PRIMARY KEY (nom_voie, code_postal, nom_commune)
                ) WITHOUT ROWID
                """
        }
        super().__init__(cursor, tables)

    def _process_csv_row(self, row, index):
        """Traite une ligne du CSV pour l'insérer dans la table adresses."""
        if len(row) < 3:
            raise RowMalformedError("Ligne avec moins de 5 colonnes")

        # Extraction des 3 champs principaux
        nom_voie = row[0].strip()
        code_postal = row[1].strip()
        nom_commune = row[2].strip()

        # Validation
        if not code_postal or not nom_commune or not nom_voie:
            raise RowMalformedError("Champs vides détectés")

        try:
            self.cursor.execute(
                "INSERT INTO adresses (nom_voie, code_postal, nom_commune) VALUES (?, ?, ?)",
                (nom_voie, code_postal, nom_commune),
            )
            return 1
        except Exception as e:
            # Doublon ou autre erreur
            raise RowMalformedError(e)

    def _display_statistics(self):
        """Affiche les statistiques spécifiques à la table unique."""
        # Nombre total d'enregistrements
        self.cursor.execute("SELECT COUNT(*) FROM adresses")
        count = self.cursor.fetchone()[0]
        print(f"{'Adresses':20} : {count:>10,}")

        # Statistiques supplémentaires
        self.cursor.execute("SELECT COUNT(DISTINCT nom_voie) FROM adresses")
        count_rues = self.cursor.fetchone()[0]
        print(f"{'Voies distinctes':20} : {count_rues:>10,}")

        self.cursor.execute("SELECT COUNT(DISTINCT code_postal) FROM adresses")
        count_cp = self.cursor.fetchone()[0]
        print(f"{'Codes postaux':20} : {count_cp:>10,}")

        self.cursor.execute("SELECT COUNT(DISTINCT nom_commune) FROM adresses")
        count_communes = self.cursor.fetchone()[0]
        print(f"{'Communes':20} : {count_communes:>10,}")


if __name__ == "__main__":
    db_cursor = DatabaseCursor("bano_no_joins_wo_rowid.db")
    builder = BANODatabaseBuilderNoJoinsWoRowid(db_cursor)
    builder.auto_create("streets.csv")
