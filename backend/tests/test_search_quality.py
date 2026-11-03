"""Tests for search quality, strength-aware matching, and concentration guard."""

import asyncio
import json
from pathlib import Path
import socket
import sys
import time
import traceback
import pytest

# Ensure backend/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog
from agents.price_lookup import run_comparison


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Block every socket.connect whose host is not loopback."""
    orig_connect = socket.socket.connect

    def _guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError(f"Network calls are forbidden during catalog tests: {host}")
        return orig_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)


def test_parse_query():
    assert catalog.parse_query("paracetamol 650") == ("paracetamol", 650.0, None)
    assert catalog.parse_query("Levothyroxine 100 mcg") == ("levothyroxine", 100.0, "mcg")
    assert catalog.parse_query("Cetirizine") == ("cetirizine", None, None)
    assert catalog.parse_query("S(-)Amlodipine 2.5 mg") == ("levamlodipine", 2.5, "mg")


def test_search_paracetamol_single_ingredient_first():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol", items)
    assert len(results) > 0
    first = results[0]
    assert first["is_combination"] is False
    assert any(c.get("salt") == "paracetamol" for c in first.get("components", []))


def test_search_paracetamol_650_exact():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert results[0]["sr_no"] == 398
    for item in results:
        assert any(
            c.get("salt") == "paracetamol" and c.get("strength") == 650.0
            for c in item.get("components", [])
        )


def test_search_paracetamol_650_no_concentration():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert not any(item.get("is_concentration") is True for item in results)


def test_search_paracetamol_9999_empty():
    items = catalog.load_catalog()
    assert catalog.search("paracetamol 9999", items) == []


def test_search_amlodipine_excludes_levamlodipine():
    items = catalog.load_catalog()
    results = catalog.search("amlodipine", items)
    assert len(results) > 0
    assert not any(
        any(c.get("salt") == "levamlodipine" for c in item.get("components", []))
        for item in results
    )


def test_concentration_items_have_mg_and_ml():
    import re
    items = catalog.load_catalog()
    conc_items = [item for item in items if item.get("is_concentration") is True]
    assert len(conc_items) > 0
    for item in conc_items:
        clean = item.get("name_clean", "")
        assert re.search(r"(mg|mcg|g|iu|%)", clean) is not None, clean
        assert "ml" in clean, clean


def test_import_report_combination_and_concentration_counts():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert "combination_rows" in report
    assert isinstance(report["combination_rows"], int)
    assert "concentration_rows" in report
    assert isinstance(report["concentration_rows"], int)

    items = catalog.load_catalog()
    comb_count = sum(1 for item in items if item.get("is_combination") is True)
    conc_count = sum(1 for item in items if item.get("is_concentration") is True)
    assert report["combination_rows"] == comb_count
    assert report["concentration_rows"] == conc_count


def test_timing_10_medicines():
    names = [
        "Paracetamol",
        "Ibuprofen",
        "Metformin",
        "Pantoprazole",
        "Atorvastatin",
        "Amlodipine",
        "Cetirizine",
        "Levothyroxine",
        "Ondansetron",
        "Azithromycin",
    ]
    t0 = time.perf_counter()
    res = asyncio.run(run_comparison(names))
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0
    assert len(res["medicines"]) == 10

