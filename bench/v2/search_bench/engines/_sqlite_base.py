# search_bench/engines/_sqlite_base.py
import os
import sqlite3
import tempfile


def open_temp_db(name: str) -> tuple[sqlite3.Connection, str]:
    """Crée une base SQLite sur disque (pour mesurer la taille de l'artefact)."""
    path = os.path.join(tempfile.gettempdir(), f"bano_bench_{name}.db")
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    return conn, path


def file_size(path: str) -> int:
    return os.path.getsize(path) if os.path.exists(path) else -1


def open_db_at(path: str) -> sqlite3.Connection:
    """Ouvre/crée une base SQLite à un chemin précis (pour les artefacts persistés)."""
    if os.path.exists(path):
        os.remove(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA page_size = 4096")
    conn.execute("PRAGMA auto_vacuum = FULL")
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    return conn


def finalize_db(conn) -> None:
    """Compacte la base et met à jour les stats (réduit la taille de l'artefact).

    VACUUM doit tourner hors transaction -> on bascule en autocommit le temps du VACUUM.
    """
    conn.commit()
    conn.execute("ANALYZE")
    conn.commit()
    old = conn.isolation_level
    conn.isolation_level = None
    conn.execute("VACUUM")
    conn.isolation_level = old


def open_existing_db(path: str) -> sqlite3.Connection:
    """Ouvre une base SQLite existante en lecture seule (artefact figé)."""
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
