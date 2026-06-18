# search_bench/bench/run.py
"""Harness: exécute chaque méthode sur queries.json, mesure, écrit un rapport, triage."""

import json
import sys
import time
from dataclasses import asdict

from search_bench.data import load_records
from search_bench.engines import ENGINES
from search_bench.metrics import percentile, recall_at_k, reciprocal_rank


def _format_progress(label, done, total, latencies, recall_hits) -> str:
    p50 = percentile(latencies, 50) if latencies else 0.0
    recall = recall_hits / done if done else 0.0
    return f"{label}  {done}/{total}  p50={p50:.1f}ms  recall@5={recall:.2f}"


def _measure_queries(
    engine, queries, limit: int, label=None, progress: bool = False
) -> dict:
    latencies: list[float] = []
    r5: list[float] = []
    r10: list[float] = []
    rr: list[float] = []
    total = len(queries)
    step = max(1, total // 100)
    for i, item in enumerate(queries, start=1):
        start = time.perf_counter()
        results = engine.search(item["query"], limit=limit)
        latencies.append((time.perf_counter() - start) * 1000)
        dict_results = [asdict(r) for r in results]
        target = item["target"]
        r5.append(recall_at_k(dict_results, target, 5))
        r10.append(recall_at_k(dict_results, target, 10))
        rr.append(reciprocal_rank(dict_results, target))
        if progress and label and (i % step == 0 or i == total):
            sys.stdout.write(
                "\r" + _format_progress(label, i, total, latencies, sum(r5))
            )
            sys.stdout.flush()
    if progress and label:
        sys.stdout.write("\n")
        sys.stdout.flush()
    n = max(1, total)
    return {
        "n_queries": total,
        "latency_p50_ms": round(percentile(latencies, 50), 3),
        "latency_p95_ms": round(percentile(latencies, 95), 3),
        "latency_p99_ms": round(percentile(latencies, 99), 3),
        "recall_at_5": round(sum(r5) / n, 4),
        "recall_at_10": round(sum(r10) / n, 4),
        "mrr": round(sum(rr) / n, 4),
    }


def benchmark_engine(
    engine_cls, records, queries, limit: int = 10, label=None, progress: bool = False
) -> dict:
    engine = engine_cls()
    engine.build(records)
    try:
        metrics = _measure_queries(
            engine, queries, limit, label=label, progress=progress
        )
        return {
            "name": engine_cls.name,
            "supports_fuzzy": engine_cls.supports_fuzzy,
            "build_time_ms": round(engine.build_time_ms, 2),
            "artifact_size_bytes": engine.artifact_size_bytes,
            "load_ms": None,
            **metrics,
        }
    finally:
        engine.close()


def benchmark_artifact(
    engine_cls,
    artifact_dir,
    queries,
    limit: int = 10,
    label=None,
    progress: bool = False,
) -> dict:
    load_start = time.perf_counter()
    engine = engine_cls.load(artifact_dir)
    load_ms = round((time.perf_counter() - load_start) * 1000, 2)
    try:
        metrics = _measure_queries(
            engine, queries, limit, label=label, progress=progress
        )
        return {
            "name": engine_cls.name,
            "supports_fuzzy": engine_cls.supports_fuzzy,
            "build_time_ms": round(engine.build_time_ms, 2),
            "artifact_size_bytes": engine.artifact_size_bytes,
            "load_ms": load_ms,
            **metrics,
        }
    finally:
        engine.close()


def _require_artifacts_dir(artifacts_dir: str) -> None:
    import os

    manifest = os.path.join(artifacts_dir, "manifest.json")
    if not os.path.exists(manifest):
        raise SystemExit(
            f"Aucun artefact prebuild dans '{artifacts_dir}' (manifest.json absent). "
            f"Lance d'abord : python -m search_bench.prebuild -i <streets.csv> -o {artifacts_dir}"
        )


def select_survivors(
    reports: list[dict], min_recall_at_5: float = 0.5, max_p95_ms: float = 50.0
) -> list[str]:
    """Survivantes = qualité ET latence acceptables (seuils ajustables)."""
    return [
        r["name"]
        for r in reports
        if r["recall_at_5"] >= min_recall_at_5 and r["latency_p95_ms"] <= max_p95_ms
    ]


def _markdown(reports: list[dict], survivors: list[str]) -> str:
    lines = [
        "# Rapport benchmark recherche BANO",
        "",
        "| Méthode | fuzzy | build ms | load ms | taille | p50 ms | p95 ms | p99 ms | recall@5 | recall@10 | MRR |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in reports:
        size = (
            "mémoire"
            if r["artifact_size_bytes"] < 0
            else f"{r['artifact_size_bytes'] / 1e6:.1f} Mo"
        )
        load = "—" if r.get("load_ms") is None else r["load_ms"]
        lines.append(
            f"| {r['name']} | {'✅' if r['supports_fuzzy'] else '—'} | {r['build_time_ms']} | {load} | {size} "
            f"| {r['latency_p50_ms']} | {r['latency_p95_ms']} | {r['latency_p99_ms']} "
            f"| {r['recall_at_5']} | {r['recall_at_10']} | {r['mrr']} |"
        )
    lines += [
        "",
        f"**Survivantes :** {', '.join(survivors) if survivors else 'aucune'}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Benchmark desktop des méthodes de recherche"
    )
    parser.add_argument("-i", "--input", default="../../data/streets.csv")
    parser.add_argument("-q", "--queries", default="shared/queries.json")
    parser.add_argument("-o", "--out-dir", default="reports")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "-m",
        "--max-records",
        type=int,
        default=None,
        help="limite les lignes chargées (chemin build uniquement)",
    )
    parser.add_argument(
        "--artifacts",
        default=None,
        help="Dossier d'artefacts prebuild ; si fourni, charge au lieu de reconstruire",
    )
    args = parser.parse_args()

    with open(args.queries, encoding="utf-8") as f:
        queries = json.load(f)

    reports = []
    total_engines = len(ENGINES)
    if args.artifacts:
        _require_artifacts_dir(args.artifacts)
        for i, engine_cls in enumerate(ENGINES, start=1):
            label = f"[{i}/{total_engines}] {engine_cls.name} (load)"
            engine_dir = os.path.join(args.artifacts, engine_cls.name)
            reports.append(
                benchmark_artifact(
                    engine_cls,
                    engine_dir,
                    queries,
                    limit=args.limit,
                    label=label,
                    progress=True,
                )
            )
    else:
        records = load_records(args.input, limit=args.max_records)
        for i, engine_cls in enumerate(ENGINES, start=1):
            label = f"[{i}/{total_engines}] {engine_cls.name} (build)"
            reports.append(
                benchmark_engine(
                    engine_cls,
                    records,
                    queries,
                    limit=args.limit,
                    label=label,
                    progress=True,
                )
            )

    survivors = select_survivors(reports)
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"reports": reports, "survivors": survivors},
            f,
            ensure_ascii=False,
            indent=2,
        )
    with open(os.path.join(args.out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(_markdown(reports, survivors))
    print(f"✓ Rapport écrit dans {args.out_dir}/  | survivantes: {survivors}")


if __name__ == "__main__":
    main()
