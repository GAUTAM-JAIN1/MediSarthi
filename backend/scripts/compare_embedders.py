#!/usr/bin/env python
"""
compare_embedders.py — Embedder retrieval overlap comparison harness.

Compares retrieval overlap and top-1 snippets between Chroma's default embedder (A)
and Ollama's mxbai-embed-large (B) on the MediSarthi knowledge base.
DOES NOT measure latency, RSS, or declare a winner.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import urllib.parse
import urllib.request

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

FIXED_NOTE = "EVIDENCE ONLY. No winner. Human review of top-1 snippets is required before any embedder decision."


def validate_localhost(host: str) -> str:
    """Ensure ollama-host is strictly localhost or 127.0.0.1."""
    parsed = urllib.parse.urlparse(host)
    hostname = parsed.hostname or ""
    if hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError(f"Only localhost is allowed for ollama-host, got: {hostname}")
    return host


class OllamaEmbeddingFunction(EmbeddingFunction[Documents]):
    """Custom Chroma embedding function querying a local Ollama instance."""

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for text in input:
            url = f"{self.host}/api/embeddings"
            payload = json.dumps({"model": self.model, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "MediSarthi-Harness"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                embeddings.append(data["embedding"])
        return embeddings


def check_mxbai_available(host: str) -> bool:
    """Check whether mxbai-embed-large is present in local Ollama tags."""
    url = f"{host.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MediSarthi-Harness"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("models", []):
                name = m.get("name", "")
                if name == "mxbai-embed-large" or name.startswith("mxbai-embed-large:"):
                    return True
            return False
    except Exception:
        return False


def load_kb_chunks(kb_dir: Path) -> List[tuple[str, str]]:
    """Read all text files in KB directory, split on blank lines, keep chunks 40..1200 chars."""
    chunks: List[tuple[str, str]] = []
    for f in sorted(kb_dir.rglob("*.txt")):
        rel_path = f.relative_to(kb_dir).as_posix()
        text = f.read_text(encoding="utf-8")
        raw_parts = re.split(r"\n\s*\n", text)
        for idx, part in enumerate(raw_parts):
            p_strip = part.strip()
            if 40 <= len(p_strip) <= 1200:
                doc_id = f"{rel_path}#{idx}"
                chunks.append((doc_id, p_strip))
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Compare retrieval overlap between Chroma default and Ollama mxbai-embed-large."
    )
    parser.add_argument(
        "--queries",
        type=str,
        default="data/demo/embedder_queries.json",
        help="Path to JSON file containing queries array.",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for the comparison JSON report (required).",
    )
    parser.add_argument(
        "--ollama-host",
        type=str,
        default="http://127.0.0.1:11434",
        help="Localhost Ollama endpoint (default: http://127.0.0.1:11434).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of nearest neighbors to retrieve per query (default: 5).",
    )

    args = parser.parse_args()

    # Validate host
    ollama_host = validate_localhost(args.ollama_host)

    # Locate paths
    base_dir = Path(__file__).resolve().parents[1]
    q_path = Path(args.queries)
    if not q_path.is_absolute():
        q_path = base_dir / q_path

    if not q_path.is_file():
        raise FileNotFoundError(f"Queries file not found at: {q_path}")

    with open(q_path, "r", encoding="utf-8") as f:
        q_raw = json.load(f)

    if isinstance(q_raw, dict) and "queries" in q_raw:
        queries = q_raw["queries"]
    elif isinstance(q_raw, list):
        queries = q_raw
    else:
        raise ValueError(f"Unrecognized queries file shape: {type(q_raw)}")

    # Locate KB directory
    kb_dir = base_dir / "knowledge" / "medical_kb"
    if not kb_dir.is_dir():
        raise FileNotFoundError(f"KB directory not found: {kb_dir}")

    chunks = load_kb_chunks(kb_dir)
    doc_count = len(chunks)
    if doc_count == 0:
        raise RuntimeError(f"No valid chunks found in KB directory: {kb_dir}")

    doc_ids = [c[0] for c in chunks]
    doc_texts = [c[1] for c in chunks]

    temp_dir = tempfile.mkdtemp(prefix="chroma_cmp_")

    try:
        # Collection A: chromadb default
        db_path_a = os.path.join(temp_dir, "db_a")
        client_a = chromadb.PersistentClient(path=db_path_a)
        col_a = client_a.get_or_create_collection(name="kb_default")
        col_a.add(ids=doc_ids, documents=doc_texts)
        a_model = "chromadb-default"

        # Collection B: Ollama mxbai-embed-large (if available)
        mxbai_ok = check_mxbai_available(ollama_host)
        col_b = None
        if mxbai_ok:
            b_status = "mxbai-embed-large"
            db_path_b = os.path.join(temp_dir, "db_b")
            client_b = chromadb.PersistentClient(path=db_path_b)
            ef_b = OllamaEmbeddingFunction(host=ollama_host, model="mxbai-embed-large")
            col_b = client_b.get_or_create_collection(name="kb_ollama_mxbai", embedding_function=ef_b)
            col_b.add(ids=doc_ids, documents=doc_texts)
        else:
            b_status = "UNAVAILABLE: mxbai-embed-large not pulled"

        # Query both collections
        per_query_results = []
        overlap_values = []

        for q in queries:
            # Query A
            res_a = col_a.query(query_texts=[q], n_results=args.top_k)
            a_top_k = res_a["ids"][0] if res_a.get("ids") else []
            a_snippets = res_a["documents"][0] if res_a.get("documents") else []
            a_top_1_snippet = a_snippets[0][:120] if a_snippets else ""

            # Query B
            if col_b is not None:
                res_b = col_b.query(query_texts=[q], n_results=args.top_k)
                b_top_k = res_b["ids"][0] if res_b.get("ids") else []
                b_snippets = res_b["documents"][0] if res_b.get("documents") else []
                b_top_1_snippet = b_snippets[0][:120] if b_snippets else ""

                overlap = len(set(a_top_k) & set(b_top_k))
                overlap_values.append(overlap)
            else:
                b_top_k = None
                b_top_1_snippet = None
                overlap = None

            per_query_results.append({
                "query": q,
                "a_top_k": a_top_k,
                "b_top_k": b_top_k,
                "overlap": overlap,
                "a_top_1_snippet": a_top_1_snippet,
                "b_top_1_snippet": b_top_1_snippet,
            })

        mean_overlap = (
            round(sum(overlap_values) / len(overlap_values), 2)
            if overlap_values
            else None
        )

        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "doc_count": doc_count,
            "A_model": a_model,
            "B_status": b_status,
            "per_query": per_query_results,
            "summary": {
                "mean_overlap": mean_overlap,
            },
            "note": FIXED_NOTE,
        }

        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = base_dir / out_path

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Report written to: {out_path}")
        print(f"Chunks indexed: {doc_count}, Queries: {len(queries)}, B status: {b_status}")
        if mean_overlap is not None:
            print(f"Mean top-{args.top_k} overlap: {mean_overlap}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
