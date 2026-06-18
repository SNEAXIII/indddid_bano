from utils.DatabaseCursor import DatabaseCursor
from DatabaseBuilder.Interface.BANODatabaseBuilder import (
    BANODatabaseBuilder,
    RowMalformedError,
)


class BANODatabaseBuilderJoinsRowid(BANODatabaseBuilder):
    """Builder pour une base BANO avec une seule table sans jointures."""

    def __init__(self, cursor: DatabaseCursor):
        # Caches pour éviter les requêtes SELECT répétées - DICT pour O(1)
        self.cache_codes_postaux = {}
        self.cache_communes = {}
        self.cache_rues = {}
        tables = {
            "codes_postaux": """
                CREATE TABLE IF NOT EXISTS codes_postaux (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL
                )
                """,
            "communes": """
            CREATE TABLE IF NOT EXISTS communes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL
                )
                """,
            "voies": """
            CREATE TABLE IF NOT EXISTS voies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL
                )
                """,
            "adresses": """
                CREATE TABLE IF NOT EXISTS adresses (
                    id_nom_voie INTEGER NOT NULL,
                    id_code_postal INTEGER NOT NULL,
                    id_nom_commune INTEGER NOT NULL,
                    PRIMARY KEY (id_nom_voie, id_code_postal, id_nom_commune),
                    FOREIGN KEY (id_nom_voie) REFERENCES voies(id),
                    FOREIGN KEY (id_code_postal) REFERENCES communes(id),
                    FOREIGN KEY (id_nom_commune) REFERENCES codes_postaux(id)
                ) WITHOUT ROWID
                """,
        }

        super().__init__(cursor, tables)

    def reset_db(self):
        """Supprime et recrée les tables de la base de données."""
        # Réinitialiser les caches
        self.cache_codes_postaux = {}
        self.cache_communes = {}
        self.cache_rues = {}
        super().reset_db()

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
            # Récupérer ou créer un ID pour le code postal (O(1))
            if code_postal not in self.cache_codes_postaux:
                id_code_postal = len(self.cache_codes_postaux)
                self.cache_codes_postaux[code_postal] = id_code_postal
                self.cursor.execute(
                    "INSERT INTO codes_postaux (id, code) VALUES (?, ?)",
                    (id_code_postal, code_postal),
                )
            else:
                id_code_postal = self.cache_codes_postaux[code_postal]

            # Récupérer ou créer un ID pour la commune (O(1))
            if nom_commune not in self.cache_communes:
                id_commune = len(self.cache_communes)
                self.cache_communes[nom_commune] = id_commune
                self.cursor.execute(
                    "INSERT INTO communes (id, nom) VALUES (?, ?)",
                    (id_commune, nom_commune),
                )
            else:
                id_commune = self.cache_communes[nom_commune]

            # Récupérer ou créer un ID pour la voie (O(1))
            if nom_voie not in self.cache_rues:
                id_rue = len(self.cache_rues)
                self.cache_rues[nom_voie] = id_rue
                self.cursor.execute(
                    "INSERT INTO voies (id, nom) VALUES (?, ?)", (id_rue, nom_voie)
                )
            else:
                id_rue = self.cache_rues[nom_voie]

            # Insérer l'adresse
            self.cursor.execute(
                "INSERT INTO adresses (id_nom_voie, id_code_postal, id_nom_commune) VALUES (?, ?, ?)",
                (id_rue, id_code_postal, id_commune),
            )
            return 1
        except Exception as e:
            raise RowMalformedError(e)

    def _display_statistics(self):
        """Affiche les statistiques spécifiques à la table unique."""
        # Nombre total d'enregistrements
        self.cursor.execute("SELECT COUNT(*) FROM adresses")
        count = self.cursor.fetchone()[0]
        print(f"{'Adresses':20} : {count:>10,}")

        # Statistiques supplémentaires
        self.cursor.execute("SELECT COUNT(*) FROM voies")
        count_rues = self.cursor.fetchone()[0]
        print(f"{'Voies distinctes':20} : {count_rues:>10,}")

        self.cursor.execute("SELECT COUNT(*) FROM codes_postaux")
        count_cp = self.cursor.fetchone()[0]
        print(f"{'Codes postaux':20} : {count_cp:>10,}")

        self.cursor.execute("SELECT COUNT(*) FROM communes")
        count_communes = self.cursor.fetchone()[0]
        print(f"{'Communes':20} : {count_communes:>10,}")


if __name__ == "__main__":
    db_cursor = DatabaseCursor("bano_joins_rowid.db")
    builder = BANODatabaseBuilderJoinsRowid(db_cursor)
    builder.auto_create("streets.csv")
