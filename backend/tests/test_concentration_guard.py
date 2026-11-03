"""Tests for concentration guard (per-volume notation, liquid exclusion) and strength fallback."""

import csv
import json
from pathlib import Path
import re
import socket
import sys
import pytest

# Ensure backend/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog


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


def test_loose_matches_have_is_concentration_true():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "janaushadhi" / "PMBJP_Product_List_2026-11-02.csv"
    loose_re = re.compile(r"mg\s*/\s*\d*\.?\d*\s*ml|\d\s*mg\s*per\s*\d*\.?\d*\s*ml", re.IGNORECASE)
    items = catalog.load_catalog()
    items_by_sr = {item["sr_no"]: item for item in items}

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if loose_re.search(row["Generic Name"].strip()):
                sr = int(row["Sr No"].strip())
                assert items_by_sr[sr]["is_concentration"] is True


def test_search_paracetamol_250_no_concentration_or_liquid():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 250", items)
    assert {r["sr_no"] for r in results} == {519, 1051}
    assert all(catalog.is_liquid_form(r) for r in results)


def test_search_paracetamol_250_first_result():
    items = catalog.load_catalog()
    liquid_250 = [
        item for item in items
        if item.get("dosage_form") == "Liquid"
        and any(c.get("salt") == "paracetamol" and c.get("strength") == 250.0 for c in item.get("components", []))
    ]
    assert len(liquid_250) == 2
    results = catalog.search("paracetamol 250", items)
    assert {r["sr_no"] for r in results} == {519, 1051}
    assert all(catalog.is_liquid_form(r) for r in results)


def test_search_ibuprofen_100_no_concentration():
    items = catalog.load_catalog()
    results = catalog.search("ibuprofen 100", items)
    assert len(results) > 0
    ranks = [catalog._form_rank(r) for r in results]
    assert ranks == sorted(ranks)


def test_search_paracetamol_650_regression():
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert results[0]["sr_no"] == 398


def test_search_paracetamol_9999_regression():
    items = catalog.load_catalog()
    assert catalog.search("paracetamol 9999", items) == []


def test_search_omega_3():
    items = catalog.load_catalog()
    results = catalog.search("omega 3", items)
    assert len(results) >= 1


def test_report_concentration_rows_count():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    items = catalog.load_catalog()
    conc_count = sum(1 for item in items if item.get("is_concentration") is True)
    assert report["concentration_rows"] == conc_count

