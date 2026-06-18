# tests/test_bench.py
from search_bench.bench.run import benchmark_engine
from search_bench.engines.csv_scan import CsvLinearScan


def test_benchmark_engine_produces_metrics(records):
    queries = [
        {
            "query": "rue de la paix paris",
            "kind": "exact",
            "target": {
                "voie": "Rue de la Paix",
                "code_postal": "75002",
                "ville": "Paris",
            },
        },
    ]
    report = benchmark_engine(CsvLinearScan, records, queries, limit=10)
    assert report["name"] == "csv_scan"
    assert report["build_time_ms"] >= 0
    assert "latency_p50_ms" in report and "latency_p95_ms" in report
    assert report["recall_at_5"] == 1.0
    assert 0.0 <= report["mrr"] <= 1.0


from search_bench.bench.run import benchmark_artifact


def test_benchmark_artifact_loads_and_measures(records, tmp_path):
    built = CsvLinearScan()
    built.build(records)
    artifact_dir = str(tmp_path / "csv_scan")
    built.save(artifact_dir)
    built.close()

    queries = [
        {
            "query": "rue de la paix paris",
            "kind": "exact",
            "target": {
                "voie": "Rue de la Paix",
                "code_postal": "75002",
                "ville": "Paris",
            },
        },
    ]
    report = benchmark_artifact(CsvLinearScan, artifact_dir, queries, limit=10)
    assert report["name"] == "csv_scan"
    assert report["load_ms"] >= 0
    assert report["recall_at_5"] == 1.0
    assert "latency_p95_ms" in report


import pytest

from search_bench.bench.run import _require_artifacts_dir


def test_require_artifacts_dir_missing(tmp_path):
    with pytest.raises(SystemExit):
        _require_artifacts_dir(str(tmp_path / "nope"))


def test_format_progress_string():
    from search_bench.bench.run import _format_progress

    s = _format_progress(
        "[1/9] csv_scan",
        done=50,
        total=100,
        latencies=[10.0, 20.0, 30.0],
        recall_hits=40,
    )
    assert "[1/9] csv_scan" in s
    assert "50/100" in s
    assert "recall@5=0.80" in s  # 40/50
    assert "p50=" in s


def test_format_progress_zero_done():
    from search_bench.bench.run import _format_progress

    s = _format_progress("x", done=0, total=10, latencies=[], recall_hits=0)
    assert "0/10" in s  # must not divide by zero
