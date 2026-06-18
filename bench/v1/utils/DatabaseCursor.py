import sqlite3


class DatabaseCursor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._cursor = None
        self.connect()

    def __str__(self):
        return f"DatabaseCursor({self.db_path})"

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self._cursor = self.conn.cursor()

        # Optimisations SQLite pour réduire la taille et améliorer les performances
        self.execute("PRAGMA page_size = 4096")  # Taille de page optimale (4KB)
        self.execute(
            "PRAGMA auto_vacuum = FULL"
        )  # Nettoyage auto complet (réduit la taille)
        self.execute(
            "PRAGMA journal_mode = WAL"
        )  # Write-Ahead Logging (meilleure performance)
        self.execute(
            "PRAGMA temp_store = MEMORY"
        )  # Tables temporaires en RAM (plus rapide)
        self.execute("PRAGMA synchronous = NORMAL")  # Équilibre sécurité/performance

        print(f"✓ Connexion établie à {self.db_path}")

    def vacuum(self):
        # Réinitialise les statistiques SQLite et compresse la base
        self._cursor.execute("VACUUM")

    def execute(self, query, params=()):
        return self._cursor.execute(query, params)

    def fetchone(self):
        """Récupère une ligne du résultat de la dernière requête."""
        return self._cursor.fetchone()

    def fetchall(self):
        """Récupère toutes les lignes du résultat de la dernière requête."""
        return self._cursor.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            print(f"✓ Connexion fermée à {self.db_path}")
