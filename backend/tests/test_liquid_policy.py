"""Tests for liquid policy Option B, paediatric noise-word removal, and per-volume safety notes."""

import asyncio
import hashlib
import json
from pathlib import Path
import socket
import sys
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


def test_search_paracetamol_125():
    """search('paracetamol 125'): sr_no set contains {21, 458, 476, 634, 1049}, and all results satisfy is_liquid_form."""
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 125", items)
    sr_nos = {r["sr_no"] for r in results}
    expected = {21, 458, 476, 634, 1049}
    assert expected.issubset(sr_nos)
    assert all(catalog.is_liquid_form(r) for r in results)


def test_search_paracetamol_650_rank():
    """search('paracetamol 650'): results[0]['sr_no'] == 398. Ranks are non-decreasing (solid first)."""
    items = catalog.load_catalog()
    results = catalog.search("paracetamol 650", items)
    assert len(results) > 0
    assert results[0]["sr_no"] == 398
    ranks = [catalog._form_rank(r) for r in results]
    assert ranks == sorted(ranks)


def test_search_paracetamol_9999():
    """search('paracetamol 9999') == []."""
    items = catalog.load_catalog()
    assert catalog.search("paracetamol 9999", items) == []


def test_run_comparison_paracetamol_250():
    """asyncio.run(run_comparison(['Paracetamol 250'])): exactly 2 results; every result's notes contains 'Dose is in ml, not tablets'; key set matches."""
    res = asyncio.run(run_comparison(["Paracetamol 250"]))
    meds = res["medicines"]
    assert len(meds) == 1
    results = meds[0]["results"]
    assert len(results) == 2
    expected_keys = {
        "site",
        "product_name",
        "price",
        "quantity",
        "delivery_info",
        "product_url",
        "available",
        "notes",
    }
    for r in results:
        assert set(r.keys()) == expected_keys
        assert "Dose is in ml, not tablets" in r["notes"]


def test_run_comparison_latanoprost():
    """asyncio.run(run_comparison(['Latanoprost'])): at least one result whose product_name contains 'Drops' has notes containing 'Not a tablet strength'."""
    res = asyncio.run(run_comparison(["Latanoprost"]))
    meds = res["medicines"]
    assert len(meds) == 1
    results = meds[0]["results"]
    drops_matches = [
        r for r in results
        if "Drops" in r["product_name"] and "Not a tablet strength" in r["notes"]
    ]
    assert len(drops_matches) > 0, "No Drops result with 'Not a tablet strength' note"


def test_catalog_hash_updated():
    """The report's output_sha256 is NOT '779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043', and equals disk SHA256."""
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "janaushadhi.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    with open(catalog_path, "rb") as f:
        disk_hash = hashlib.sha256(f.read()).hexdigest()

    assert report["output_sha256"] != "779df16a87e4f7d8cd7283ab461c1a416da504a355ed49df11033a9fa1dcf043"
    assert report["output_sha256"] == disk_hash


def test_no_paediatric_salt_in_catalog():
    """No component salt in the catalog contains 'paediatric' or 'pediatric'."""
    items = catalog.load_catalog()
    for item in items:
        for c in item.get("components", []):
            salt = c.get("salt", "")
            assert "paediatric" not in salt, f"Item {item.get('sr_no')} has paediatric salt: {salt}"
            assert "pediatric" not in salt, f"Item {item.get('sr_no')} has pediatric salt: {salt}"

