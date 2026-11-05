#!/usr/bin/env python
"""
compare_embedders.py — Embedder comparison harness (evidence only).

Measures latency, memory RSS, and dimension for candidate embedding models.
DOES NOT rank, declare a winner, or make an architectural decision.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

try:
    import psutil
except ImportError:
    psutil = None


def get_rss_mb() -> Optional[float]:
    """Return process resident set size in megabytes, or None if unavailable."""
    if psutil is not None:
        return round(psutil.Process().memory_info().rss / (1024 * 1024), 2)
    return None


def percentile(vals: List[float], p: float) -> float:
    """Compute p-th percentile of sorted values."""
    if not vals:
        return 0.0
    s = sorted(vals)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    d = k - f
    return round(s[f] * (1 - d) + s[c] * d, 2)


def get_ollama_tags(host: str) -> List[str]:
    """Retrieve list of model names currently available in Ollama."""
    url = f"{host.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MediSarthi-Harness"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("models", [])
            names = []
            for m in models:
                name = m.get("name", "")
                names.append(name)
                if ":" in name:
                    names.append(name.split(":")[0])
            return names
    except Exception:
        return []


def query_ollama_embedding(host: str, model: str, text: str) -> Optional[List[float]]:
    """Query Ollama /api/embeddings for a single text."""
    url = f"{host.rstrip('/')}/api/embeddings"
    payload = json.dumps({"model": model, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("embedding")


def benchmark_ollama_candidate(
    host: str,
    candidate: str,
    queries: List[str],
) -> Dict[str, Any]:
    """Benchmark an Ollama-backed model across given queries."""
    before_rss = get_rss_mb()

    # Load time / cold start
    t0 = time.perf_counter()
    cold_embedding = query_ollama_embedding(host, candidate, queries[0])
    cold_latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    if not cold_embedding:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Ollama model {candidate} returned empty embedding",
            "metrics": None,
        }

    dim = len(cold_embedding)
    latencies_ms = [cold_latency_ms]

    # Warm runs for remaining queries
    for q in queries[1:]:
        t_start = time.perf_counter()
        emb = query_ollama_embedding(host, candidate, q)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        if emb:
            latencies_ms.append(elapsed_ms)

    after_rss = get_rss_mb()
    delta_rss = round(after_rss - before_rss, 2) if (after_rss and before_rss) else None

    return {
        "status": "AVAILABLE",
        "backend": "ollama",
        "reason": None,
        "metrics": {
            "output_dimension": dim,
            "cold_start_latency_ms": cold_latency_ms,
            "warm_latencies_ms": latencies_ms[1:],
            "per_query_latency_ms": {
                "min": min(latencies_ms),
                "max": max(latencies_ms),
                "mean": round(sum(latencies_ms) / len(latencies_ms), 2),
                "p50": percentile(latencies_ms, 50),
                "p95": percentile(latencies_ms, 95),
            },
            "memory_rss_before_mb": before_rss,
            "memory_rss_after_mb": after_rss,
            "memory_rss_delta_mb": delta_rss,
        },
    }


def evaluate_candidate(
    candidate: str,
    queries: List[str],
    ollama_host: str,
    ollama_models: List[str],
    device: str,
) -> Dict[str, Any]:
    """Check availability and benchmark candidate if available."""
    # Check Ollama first
    if candidate in ollama_models or f"{candidate}:latest" in ollama_models:
        try:
            return benchmark_ollama_candidate(ollama_host, candidate, queries)
        except Exception as e:
            return {
                "status": "UNAVAILABLE",
                "backend": "ollama",
                "reason": f"Ollama error: {e}",
                "metrics": None,
            }

    # Next check sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except ImportError:
        return {
            "status": "UNAVAILABLE",
            "backend": "none",
            "reason": f"Not pulled in Ollama and sentence-transformers package not installed",
            "metrics": None,
        }

    # If sentence_transformers is installed, try loading model
    try:
        before_rss = get_rss_mb()
        t0 = time.perf_counter()
        model = SentenceTransformer(candidate, device=device)
        load_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        latencies_ms = []
        cold_latency_ms = None
        dim = None

        for idx, q in enumerate(queries):
            t_start = time.perf_counter()
            vec = model.encode(q)
            elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            latencies_ms.append(elapsed_ms)
            if idx == 0:
                cold_latency_ms = elapsed_ms
                dim = len(vec)

        after_rss = get_rss_mb()
        delta_rss = round(after_rss - before_rss, 2) if (after_rss and before_rss) else None

        return {
            "status": "AVAILABLE",
            "backend": "sentence-transformers",
            "reason": None,
            "metrics": {
                "load_time_ms": load_time_ms,
                "output_dimension": dim,
                "cold_start_latency_ms": cold_latency_ms,
                "warm_latencies_ms": latencies_ms[1:],
                "per_query_latency_ms": {
                    "min": min(latencies_ms),
                    "max": max(latencies_ms),
                    "mean": round(sum(latencies_ms) / len(latencies_ms), 2),
                    "p50": percentile(latencies_ms, 50),
                    "p95": percentile(latencies_ms, 95),
                },
                "memory_rss_before_mb": before_rss,
                "memory_rss_after_mb": after_rss,
                "memory_rss_delta_mb": delta_rss,
            },
        }
    except Exception as e:
        return {
            "status": "UNAVAILABLE",
            "backend": "sentence-transformers",
            "reason": f"SentenceTransformer load error: {e}",
            "metrics": None,
        }


def main():
    parser = argparse.ArgumentParser(description="Compare embedding model candidates (evidence only).")
    parser.add_argument(
        "--candidates",
        type=str,
        default="bge-m3,mxbai-embed-large,all-minilm,nomic-embed-text",
        help="Comma-separated list of candidate model names.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use for sentence-transformers models (default: cpu).",
    )
    parser.add_argument(
        "--queries-file",
        type=str,
        default="data/demo/embedder_queries.json",
        help="Path to JSON file containing test queries.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../Project-docs/dumps/raw/P09/embedder_report.json",
        help="Path to write output JSON report.",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default="http://127.0.0.1:11434",
        help="Ollama host endpoint URL.",
    )

    args = parser.parse_args()

    candidates_list = [c.strip() for c in args.candidates.split(",") if c.strip()]

    # Load queries
    q_path = Path(args.queries_file)
    if not q_path.is_absolute():
        q_path = Path(__file__).resolve().parents[1] / args.queries_file

    if not q_path.is_file():
        raise FileNotFoundError(f"Queries file not found at: {q_path}")

    with open(q_path, "r", encoding="utf-8") as f:
        q_data = json.load(f)
    queries = q_data.get("queries", [])

    # Check Ollama available models
    ollama_models = get_ollama_tags(args.ollama_host)

    results: Dict[str, Any] = {}
    for cand in candidates_list:
        print(f"Evaluating candidate: {cand} ...")
        res = evaluate_candidate(
            candidate=cand,
            queries=queries,
            ollama_host=args.ollama_host,
            ollama_models=ollama_models,
            device=args.device,
        )
        results[cand] = res
        print(f"  Status: {res['status']} ({res.get('backend')})")
        if res["status"] == "AVAILABLE" and res.get("metrics"):
            m = res["metrics"]["per_query_latency_ms"]
            print(f"  Mean latency: {m['mean']} ms, p95: {m['p95']} ms, Dim: {res['metrics']['output_dimension']}")
        elif res.get("reason"):
            print(f"  Reason: {res['reason']}")

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "device": args.device,
        "ollama_host": args.ollama_host,
        "queries_count": len(queries),
        "candidates": results,
        "note": "EVIDENCE ONLY. No winner declared. Decision on production embedder is pending.",
    }

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = Path(__file__).resolve().parents[1] / args.output

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport written to: {out_path}")


if __name__ == "__main__":
    main()
