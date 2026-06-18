#!/usr/bin/env python3
"""
Benchmark de comparaison des différentes stratégies de stockage BANO.

Compare les fichiers générés :
- SQLite : bano_joins2_rowid.db, bano_joins_rowid.db, bano_no_joins_rowid.db, bano_no_joins_wo_rowid.db
- Parquet : bano_simple.parquet
- Arrow IPC : bano_simple.arrow

Métriques mesurées :
- Taille du fichier
- Temps de lecture complète
- Temps de requêtes types (recherche, agrégation)
"""

import os
import sqlite3
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Any

import pyarrow.parquet as pq
import pyarrow.ipc as ipc
import pyarrow.compute as pc


@dataclass
class BenchmarkResult:
    """Résultat d'un benchmark pour un fichier."""

    name: str
    file_path: str
    file_size_mb: float = 0.0
    record_count: int = 0
    read_all_time: float = 0.0
    search_time: float = 0.0
    aggregate_time: float = 0.0
    distinct_rues: int = 0
    distinct_cp: int = 0
    distinct_communes: int = 0


@dataclass
class BenchmarkSuite:
    """Suite de benchmarks pour tous les fichiers."""

    results: list[BenchmarkResult] = field(default_factory=list)

    def add_result(self, result: BenchmarkResult):
        self.results.append(result)

    def print_summary(self):
        """Affiche un résumé comparatif des benchmarks."""
        sep = "=" * 100
        print("\n" + sep)
        print("📊 BENCHMARK COMPARATIF - BANO PARSER")
        print(sep)

        # Tableau des tailles
        print("\n📦 TAILLE DES FICHIERS")
        print("-" * 60)
        print(f"{'Stratégie':<30} {'Taille (Mo)':>15} {'Ratio':>10}")
        print("-" * 60)

        min_size = min(r.file_size_mb for r in self.results if r.file_size_mb > 0)
        for r in sorted(self.results, key=lambda x: x.file_size_mb):
            ratio = r.file_size_mb / min_size if min_size > 0 else 0
            print(f"{r.name:<30} {r.file_size_mb:>12.2f} Mo {ratio:>8.2f}x")

        # Tableau des temps de lecture
        print("\n⏱️ TEMPS DE LECTURE COMPLÈTE")
        print("-" * 60)
        print(f"{'Stratégie':<30} {'Temps (s)':>15} {'Ratio':>10}")
        print("-" * 60)

        min_time = min(r.read_all_time for r in self.results if r.read_all_time > 0)
        for r in sorted(self.results, key=lambda x: x.read_all_time):
            ratio = r.read_all_time / min_time if min_time > 0 else 0
            print(f"{r.name:<30} {r.read_all_time:>12.4f} s {ratio:>8.2f}x")

        # Tableau des temps de recherche
        print("\n🔍 TEMPS DE RECHERCHE (recherche par code postal)")
        print("   ℹ️  Parquet utilise le predicate pushdown (filtrage avant chargement)")
        print("-" * 60)
        print(f"{'Stratégie':<30} {'Temps (ms)':>15} {'Ratio':>10}")
        print("-" * 60)

        min_search = min(r.search_time for r in self.results if r.search_time > 0)
        for r in sorted(self.results, key=lambda x: x.search_time):
            ratio = r.search_time / min_search if min_search > 0 else 0
            print(f"{r.name:<30} {r.search_time * 1000:>12.2f} ms {ratio:>8.2f}x")

        # Tableau des temps d'agrégation
        print("\n📈 TEMPS D'AGRÉGATION (COUNT DISTINCT)")
        print("-" * 60)
        print(f"{'Stratégie':<30} {'Temps (ms)':>15} {'Ratio':>10}")
        print("-" * 60)

        min_agg = min(r.aggregate_time for r in self.results if r.aggregate_time > 0)
        for r in sorted(self.results, key=lambda x: x.aggregate_time):
            ratio = r.aggregate_time / min_agg if min_agg > 0 else 0
            print(f"{r.name:<30} {r.aggregate_time * 1000:>12.2f} ms {ratio:>8.2f}x")

        # Statistiques des données
        print("\n📋 STATISTIQUES DES DONNÉES")
        print("-" * 80)
        print(
            f"{'Stratégie':<30} {'Adresses':>12} {'Voies':>12} {'CP':>10} {'Communes':>12}"
        )
        print("-" * 80)
        for r in self.results:
            print(
                f"{r.name:<30} {r.record_count:>12,} {r.distinct_rues:>12,} {r.distinct_cp:>10,} {r.distinct_communes:>12,}"
            )

        # Résumé final
        print("\n" + sep)
        print("🏆 RÉSUMÉ")
        print(sep)

        smallest = min(self.results, key=lambda x: x.file_size_mb)
        fastest_read = min(self.results, key=lambda x: x.read_all_time)
        fastest_search = min(self.results, key=lambda x: x.search_time)
        fastest_agg = min(self.results, key=lambda x: x.aggregate_time)

        print(
            f"  📦 Plus petit fichier    : {smallest.name} ({smallest.file_size_mb:.2f} Mo)"
        )
        print(
            f"  ⏱️ Lecture la plus rapide : {fastest_read.name} ({fastest_read.read_all_time:.4f} s)"
        )
        print(
            f"  🔍 Recherche la plus rapide: {fastest_search.name} ({fastest_search.search_time * 1000:.2f} ms)"
        )
        print(
            f"  📈 Agrégation la plus rapide: {fastest_agg.name} ({fastest_agg.aggregate_time * 1000:.2f} ms)"
        )
        print(sep + "\n")


def timeit(func: Callable, *args, **kwargs) -> tuple[float, Any]:
    """Mesure le temps d'exécution d'une fonction."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return elapsed, result


def benchmark_sqlite_no_joins(db_path: str, name: str) -> BenchmarkResult:
    """Benchmark pour les bases SQLite sans jointures (table unique)."""
    result = BenchmarkResult(name=name, file_path=db_path)

    if not Path(db_path).exists():
        print(f"⚠️  Fichier non trouvé: {db_path}")
        return result

    result.file_size_mb = os.path.getsize(db_path) / (1024 * 1024)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Lecture complète
    elapsed, rows = timeit(lambda: cursor.execute("SELECT * FROM adresses").fetchall())
    result.read_all_time = elapsed
    result.record_count = len(rows)

    # 2. Recherche par code postal
    elapsed, _ = timeit(
        lambda: cursor.execute(
            "SELECT * FROM adresses WHERE code_postal = '75001'"
        ).fetchall()
    )
    result.search_time = elapsed

    # 3. Agrégation (COUNT DISTINCT)
    elapsed, _ = timeit(
        lambda: cursor.execute("""
        SELECT 
            COUNT(DISTINCT nom_voie) as voies,
            COUNT(DISTINCT code_postal) as cp,
            COUNT(DISTINCT nom_commune) as communes
        FROM adresses
    """).fetchone()
    )
    result.aggregate_time = elapsed

    # Statistiques
    cursor.execute("SELECT COUNT(DISTINCT nom_voie) FROM adresses")
    result.distinct_rues = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT code_postal) FROM adresses")
    result.distinct_cp = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT nom_commune) FROM adresses")
    result.distinct_communes = cursor.fetchone()[0]

    conn.close()
    return result


def benchmark_sqlite_joins(
    db_path: str, name: str, has_rues_table: bool = True
) -> BenchmarkResult:
    """Benchmark pour les bases SQLite avec jointures."""
    result = BenchmarkResult(name=name, file_path=db_path)

    if not Path(db_path).exists():
        print(f"⚠️  Fichier non trouvé: {db_path}")
        return result

    result.file_size_mb = os.path.getsize(db_path) / (1024 * 1024)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Construction de la requête selon le schéma
    if has_rues_table:
        # JoinsRowid: 4 tables (voies, codes_postaux, communes, adresses)
        select_query = """
            SELECT r.nom, cp.code, c.nom
            FROM adresses a
            JOIN voies r ON a.id_nom_voie = r.id
            JOIN codes_postaux cp ON a.id_code_postal = cp.id
            JOIN communes c ON a.id_nom_commune = c.id
        """
        search_query = """
            SELECT r.nom, cp.code, c.nom
            FROM adresses a
            JOIN voies r ON a.id_nom_voie = r.id
            JOIN codes_postaux cp ON a.id_code_postal = cp.id
            JOIN communes c ON a.id_nom_commune = c.id
            WHERE cp.code = '75001'
        """
    else:
        # Joins2Rowid: 3 tables (codes_postaux, communes, adresses avec nom_voie direct)
        select_query = """
            SELECT a.nom_voie, cp.code, c.nom
            FROM adresses a
            JOIN codes_postaux cp ON a.id_code_postal = cp.id
            JOIN communes c ON a.id_nom_commune = c.id
        """
        search_query = """
            SELECT a.nom_voie, cp.code, c.nom
            FROM adresses a
            JOIN codes_postaux cp ON a.id_code_postal = cp.id
            JOIN communes c ON a.id_nom_commune = c.id
            WHERE cp.code = '75001'
        """

    # 1. Lecture complète avec jointures
    elapsed, rows = timeit(lambda: cursor.execute(select_query).fetchall())
    result.read_all_time = elapsed
    result.record_count = len(rows)

    # 2. Recherche par code postal
    elapsed, _ = timeit(lambda: cursor.execute(search_query).fetchall())
    result.search_time = elapsed

    # 3. Agrégation
    if has_rues_table:
        agg_query = """
            SELECT 
                (SELECT COUNT(*) FROM voies) as voies,
                (SELECT COUNT(*) FROM codes_postaux) as cp,
                (SELECT COUNT(*) FROM communes) as communes
        """
    else:
        agg_query = """
            SELECT 
                COUNT(DISTINCT a.nom_voie) as voies,
                (SELECT COUNT(*) FROM codes_postaux) as cp,
                (SELECT COUNT(*) FROM communes) as communes
            FROM adresses a
        """

    elapsed, stats = timeit(lambda: cursor.execute(agg_query).fetchone())
    result.aggregate_time = elapsed
    result.distinct_rues, result.distinct_cp, result.distinct_communes = stats

    conn.close()
    return result


def benchmark_parquet(parquet_path: str, name: str) -> BenchmarkResult:
    """Benchmark pour les fichiers Parquet avec PyArrow natif."""
    result = BenchmarkResult(name=name, file_path=parquet_path)

    if not Path(parquet_path).exists():
        print(f"⚠️  Fichier non trouvé: {parquet_path}")
        return result

    result.file_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)

    # 1. Lecture complète avec PyArrow (plus rapide que Pandas)
    def read_all():
        return pq.read_table(parquet_path)

    elapsed, table = timeit(read_all)
    result.read_all_time = elapsed
    result.record_count = table.num_rows

    # 2. Recherche par code postal avec PyArrow compute (très rapide)
    def search_pyarrow():
        t = pq.read_table(parquet_path)
        mask = pc.equal(t.column("code_postal"), "75001")
        return t.filter(mask)

    elapsed, _ = timeit(search_pyarrow)
    result.search_time = elapsed

    # 3. Agrégation avec PyArrow (plus rapide que Pandas)
    def aggregate_pyarrow():
        t = pq.read_table(parquet_path)
        return (
            len(pc.unique(t.column("nom_voie"))),
            len(pc.unique(t.column("code_postal"))),
            len(pc.unique(t.column("nom_commune"))),
        )

    elapsed, (voies, cp, communes) = timeit(aggregate_pyarrow)
    result.aggregate_time = elapsed
    result.distinct_rues = voies
    result.distinct_cp = cp
    result.distinct_communes = communes

    return result


def benchmark_parquet_duckdb(parquet_path: str, name: str) -> BenchmarkResult:
    """Benchmark pour les fichiers Parquet avec DuckDB (SQL ultra-rapide)."""
    result = BenchmarkResult(name=name, file_path=parquet_path)

    if not Path(parquet_path).exists():
        print(f"⚠️  Fichier non trouvé: {parquet_path}")
        return result

    try:
        import duckdb
    except ImportError:
        print(f"⚠️  DuckDB non installé, skipping {name}")
        return result

    result.file_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)

    # Connexion DuckDB en mémoire
    conn = duckdb.connect()

    # 1. Lecture complète
    def read_all():
        return conn.execute(f"SELECT * FROM '{parquet_path}'").fetchall()

    elapsed, rows = timeit(read_all)
    result.read_all_time = elapsed
    result.record_count = len(rows)

    # 2. Recherche par code postal (DuckDB est TRÈS rapide pour ça)
    def search_duckdb():
        return conn.execute(
            f"SELECT * FROM '{parquet_path}' WHERE code_postal = '75001'"
        ).fetchall()

    elapsed, _ = timeit(search_duckdb)
    result.search_time = elapsed

    # 3. Agrégation
    def aggregate_duckdb():
        return conn.execute(f"""
            SELECT 
                COUNT(DISTINCT nom_voie) as voies,
                COUNT(DISTINCT code_postal) as cp,
                COUNT(DISTINCT nom_commune) as communes
            FROM '{parquet_path}'
        """).fetchone()

    elapsed, stats = timeit(aggregate_duckdb)
    result.aggregate_time = elapsed
    result.distinct_rues, result.distinct_cp, result.distinct_communes = stats

    conn.close()
    return result


def benchmark_arrow(arrow_path: str, name: str) -> BenchmarkResult:
    """Benchmark pour les fichiers Arrow IPC avec PyArrow natif."""
    result = BenchmarkResult(name=name, file_path=arrow_path)

    if not Path(arrow_path).exists():
        print(f"⚠️  Fichier non trouvé: {arrow_path}")
        return result

    result.file_size_mb = os.path.getsize(arrow_path) / (1024 * 1024)

    # 1. Lecture complète avec PyArrow IPC (très rapide, zero-copy)
    def read_all():
        with ipc.open_file(arrow_path) as f:
            return f.read_all()

    elapsed, table = timeit(read_all)
    result.read_all_time = elapsed
    result.record_count = table.num_rows

    # 2. Recherche par code postal avec PyArrow compute
    def search_arrow():
        with ipc.open_file(arrow_path) as f:
            t = f.read_all()
        mask = pc.equal(t.column("code_postal"), "75001")
        return t.filter(mask)

    elapsed, _ = timeit(search_arrow)
    result.search_time = elapsed

    # 3. Agrégation avec PyArrow compute (vectorisé)
    def aggregate_arrow():
        with ipc.open_file(arrow_path) as f:
            t = f.read_all()
        return (
            len(pc.unique(t.column("nom_voie"))),
            len(pc.unique(t.column("code_postal"))),
            len(pc.unique(t.column("nom_commune"))),
        )

    elapsed, (voies, cp, communes) = timeit(aggregate_arrow)
    result.aggregate_time = elapsed
    result.distinct_rues = voies
    result.distinct_cp = cp
    result.distinct_communes = communes

    return result


def run_benchmarks():
    """Exécute tous les benchmarks."""
    print("🚀 Démarrage des benchmarks...")
    print("=" * 60)

    suite = BenchmarkSuite()

    # SQLite sans jointures
    print("\n📂 Benchmark: bano_no_joins_rowid.db")
    result = benchmark_sqlite_no_joins(
        "bano_no_joins_rowid.db", "SQLite NoJoins (ROWID)"
    )
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    print("\n📂 Benchmark: bano_no_joins_wo_rowid.db")
    result = benchmark_sqlite_no_joins(
        "bano_no_joins_wo_rowid.db", "SQLite NoJoins (WO ROWID)"
    )
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # SQLite avec jointures (4 tables)
    print("\n📂 Benchmark: bano_joins_rowid.db")
    result = benchmark_sqlite_joins(
        "bano_joins_rowid.db", "SQLite Joins 3NF (4 tables)", has_rues_table=True
    )
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # SQLite avec jointures (3 tables)
    print("\n📂 Benchmark: bano_joins2_rowid.db")
    result = benchmark_sqlite_joins(
        "bano_joins2_rowid.db", "SQLite Joins (3 tables)", has_rues_table=False
    )
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # Parquet avec PyArrow
    print("\n📂 Benchmark: bano_simple.parquet (PyArrow)")
    result = benchmark_parquet("bano_simple.parquet", "Parquet (PyArrow)")
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # Parquet avec DuckDB (optionnel, si installé)
    print("\n📂 Benchmark: bano_simple.parquet (DuckDB)")
    result = benchmark_parquet_duckdb("bano_simple.parquet", "Parquet (DuckDB)")
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # Arrow IPC
    print("\n📂 Benchmark: bano_simple.arrow")
    result = benchmark_arrow("bano_simple.arrow", "Arrow IPC")
    if result.record_count > 0:
        suite.add_result(result)
        print(
            f"   ✓ {result.record_count:,} enregistrements, {result.file_size_mb:.2f} Mo"
        )

    # Afficher le résumé
    if suite.results:
        suite.print_summary()
    else:
        all_file = [
            "DatabaseBuilder.BANODatabaseBuilderNoJoinsRowid",
            "DatabaseBuilder.BANODatabaseBuilderNoJoinsWoRowid",
            "DatabaseBuilder.BANODatabaseBuilderJoinsRowid",
            "DatabaseBuilder.BANODatabaseBuilderJoins2Rowid",
            "ParquetBuilder.BANOParquetBuilderSimple",
            "ArrowBuilder.BANOArrowBuilderSimple",
        ]
        print("\n⚠️  Aucun fichier de benchmark trouvé.")
        print("   Exécutez d'abord les builders pour générer les fichiers:")
        for file in all_file:
            print(f"uv run python -m {file}&&echo {file} done&")


if __name__ == "__main__":
    run_benchmarks()
