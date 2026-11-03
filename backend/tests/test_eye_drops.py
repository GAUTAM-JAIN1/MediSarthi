"""Tests for eye drops, nasal drops, and solution noise words."""

import asyncio
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


def test_parse_components_latanoprost_eye_drops():
    """parse_components('Latanoprost Eye Drops IP 0.005% w/v (50mcg per ml)') gives one component with salt 'latanoprost' and strength 0.005, unit '%'."""
    comps = catalog.parse_components("Latanoprost Eye Drops IP 0.005% w/v (50mcg per ml)")
    assert len(comps) == 1
    assert comps[0]["salt"] == "latanoprost"
    assert comps[0]["strength"] == 0.005
    assert comps[0]["unit"] == "%"


def test_search_latanoprost_results():
    """search('latanoprost'): the first result has sr_no 1970, and the set of sr_nos is {1970, 1810}."""
    items = catalog.load_catalog()
    results = catalog.search("latanoprost", items)
    sr_nos = [r["sr_no"] for r in results]
    assert len(results) >= 2
    assert results[0]["sr_no"] == 1970
    assert set(sr_nos) == {1970, 1810}


def test_item_1810_component_salts():
    """The item with sr_no 1810 still has component salts ['latanoprost', 'timolol maleate']."""
    items = catalog.load_catalog()
    it_1810 = next(i for i in items if i["sr_no"] == 1810)
    salts = [c.get("salt") for c in it_1810.get("components", [])]
    assert salts == ["latanoprost", "timolol maleate"]


def test_parse_and_search_xylometazoline():
    """parse_components('Xylometazoline Nasal Drops IP 0.1%w/v') gives salt 'xylometazoline'. search('xylometazoline') contains sr_no 269."""
    comps = catalog.parse_components("Xylometazoline Nasal Drops IP 0.1%w/v")
    assert any(c.get("salt") == "xylometazoline" for c in comps)
    items = catalog.load_catalog()
    results = catalog.search("xylometazoline", items)
    sr_nos = {r["sr_no"] for r in results}
    assert 269 in sr_nos


def test_run_comparison_latanoprost_drops():
    """asyncio.run(run_comparison(['Latanoprost'])): the first result's product_name contains 'Latanoprost Eye Drops', and its notes contain 'Not a tablet strength'."""
    res = asyncio.run(run_comparison(["Latanoprost"]))
    first = res["medicines"][0]["results"][0]
    assert "Latanoprost Eye Drops" in first["product_name"]
    assert "Not a tablet strength" in first["notes"]


def test_no_empty_salt_in_catalog():
    """No component salt in the catalog is an empty string."""
    items = catalog.load_catalog()
    for item in items:
        for c in item.get("components", []):
            salt = c.get("salt", "")
            assert bool(salt and salt.strip()), f"Item {item.get('sr_no')} has empty salt: {c}"


def test_search_regressions():
    """Regression: search('paracetamol 650')[0]['sr_no'] == 398, and the sr_no set of search('paracetamol 125') contains {21, 458, 476, 634, 1049}."""
    items = catalog.load_catalog()
    res_650 = catalog.search("paracetamol 650", items)
    assert len(res_650) > 0
    assert res_650[0]["sr_no"] == 398

    res_125 = catalog.search("paracetamol 125", items)
    sr_nos_125 = {r["sr_no"] for r in res_125}
    assert {21, 458, 476, 634, 1049}.issubset(sr_nos_125)

