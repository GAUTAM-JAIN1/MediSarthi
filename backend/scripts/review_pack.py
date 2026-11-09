#!/usr/bin/env python
"""
review_pack.py — Generate a human-review markdown pack for embedder decision.

Resolves top-1 document snippets to their full chunk text from the knowledge base
and outputs a template for Gautam to rate retrieval accuracy.
DOES NOT fill in ratings, rank candidates, or make an architectural decision.
"""

import argparse
import json
import os
from pathlib import Path
import sys

# Ensure backend/scripts is on path so compare_embedders can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_embedders import load_kb_chunks

RATING_LINE = "RATING_A: ____   RATING_B: ____   (sahi / partial / galat)"


def generate_review_pack(report_path: Path, out_path: Path, kb_dir: Path) -> int:
    """Generate review_pack.md from v2 report and KB chunks.

    Returns count of resolved queries.
    """
    if not report_path.is_file():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    if not kb_dir.is_dir():
        raise FileNotFoundError(f"KB directory not found: {kb_dir}")

    chunks = load_kb_chunks(kb_dir)
    chunk_map = {doc_id: text for doc_id, text in chunks}

    per_query = report.get("per_query", [])
    a_model = report.get("A_model", "Candidate A")
    b_status = report.get("B_status", "Candidate B")

    lines = [
        "# Embedder Retrieval Review Pack (Evidence Only)",
        "",
        f"- **Candidate A:** `{a_model}`",
        f"- **Candidate B:** `{b_status}`",
        f"- **Doc Count:** {report.get('doc_count', len(chunks))}",
        f"- **Mean Top-5 Overlap:** {report.get('summary', {}).get('mean_overlap', 'N/A')}",
        "",
        "> [!IMPORTANT]",
        "> Rate each candidate's top-1 retrieved document as `sahi` (accurate/relevant), `partial` (partially relevant), or `galat` (irrelevant/misleading).",
        "> Decision on production embedder will be made after human review of these 10 queries.",
        "",
        "---",
        "",
    ]

    for idx, item in enumerate(per_query, 1):
        query_text = item.get("query", "")
        overlap = item.get("overlap")
        a_top_k = item.get("a_top_k", [])
        b_top_k = item.get("b_top_k")

        a_top_1_id = a_top_k[0] if a_top_k else None
        b_top_1_id = b_top_k[0] if b_top_k else None

        a_full_text = chunk_map.get(a_top_1_id) if a_top_1_id else None
        b_full_text = chunk_map.get(b_top_1_id) if b_top_1_id else None

        overlap_str = f"{overlap}/5" if overlap is not None else "N/A"
        lines.append(f"## Query {idx}: {query_text} (Overlap: {overlap_str})")
        lines.append("")
        lines.append(f"**Top-5 IDs ({a_model}):**")
        lines.append(", ".join(f"`{x}`" for x in a_top_k) if a_top_k else "(none)")
        lines.append("")

        if b_top_k is not None:
            lines.append(f"**Top-5 IDs ({b_status}):**")
            lines.append(", ".join(f"`{x}`" for x in b_top_k) if b_top_k else "(none)")
        else:
            lines.append(f"**Top-5 IDs ({b_status}):** B UNAVAILABLE")
        lines.append("")

        # Candidate A Top-1
        lines.append(f"### Candidate A ({a_model}) -- Top-1: `{a_top_1_id}`")
        if a_full_text:
            lines.append("```text")
            lines.append(a_full_text)
            lines.append("```")
        else:
            lines.append(f"(Unable to resolve chunk for id: {a_top_1_id})")
        lines.append("")

        # Candidate B Top-1
        if b_top_1_id is not None:
            lines.append(f"### Candidate B ({b_status}) -- Top-1: `{b_top_1_id}`")
            if b_full_text:
                lines.append("```text")
                lines.append(b_full_text)
                lines.append("```")
            else:
                lines.append(f"(Unable to resolve chunk for id: {b_top_1_id})")
        else:
            lines.append(f"### Candidate B ({b_status}) -- Top-1: B UNAVAILABLE")
        lines.append("")

        lines.append(RATING_LINE)
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return len(per_query)


def main():
    parser = argparse.ArgumentParser(description="Generate human-review markdown pack from embedder report.")
    parser.add_argument(
        "--report",
        type=str,
        required=True,
        help="Path to embedder report JSON (required).",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output markdown path (required).",
    )
    parser.add_argument(
        "--kb-dir",
        type=str,
        default="knowledge/medical_kb",
        help="Path to KB directory containing reference texts.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = base_dir / report_path

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = base_dir / out_path

    kb_dir = Path(args.kb_dir)
    if not kb_dir.is_absolute():
        kb_dir = base_dir / kb_dir

    count = generate_review_pack(report_path=report_path, out_path=out_path, kb_dir=kb_dir)
    print(f"review_pack.py: generated {count} query sections at: {out_path}")


if __name__ == "__main__":
    main()
