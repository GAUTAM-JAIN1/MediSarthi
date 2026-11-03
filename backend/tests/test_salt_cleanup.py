"""Tests for salt cleanup round 2 (spray, respules, respirator)."""

from pathlib import Path
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


def test_parse_components_fluticasone_propionate_nasal_spray():
    """parse_components('Fluticasone Propionate Nasal Spray IP 50 mcg') gives salts ['fluticasone propionate']."""
    comps = catalog.parse_components("Fluticasone Propionate Nasal Spray IP 50 mcg")
    salts = [c.get("salt") for c in comps]
    assert salts == ["fluticasone propionate"]


def test_parse_components_fluticasone_furoate_nasal_spray():
    """parse_components('Fluticasone Furoate Nasal Spray 27.5mcg') gives salts ['fluticasone furoate']."""
    comps = catalog.parse_components("Fluticasone Furoate Nasal Spray 27.5mcg")
    salts = [c.get("salt") for c in comps]
    assert salts == ["fluticasone furoate"]


def test_item_421_salt():
    """The item with sr_no 421 has salt 'fluticasone propionate'."""
    items = catalog.load_catalog()
    it421 = next(i for i in items if i["sr_no"] == 421)
    salts = [c.get("salt") for c in it421.get("components", [])]
    assert salts == ["fluticasone propionate"]


def test_item_431_salt():
    """The item with sr_no 431 has salt 'ipratropium bromide'."""
    items = catalog.load_catalog()
    it431 = next(i for i in items if i["sr_no"] == 431)
    salts = [c.get("salt") for c in it431.get("components", [])]
    assert salts == ["ipratropium bromide"]


def test_search_fluticasone_propionate_contains_425_and_421():
    """search('fluticasone propionate') contains sr_no 425 and sr_no 421."""
    items = catalog.load_catalog()
    results = catalog.search("fluticasone propionate", items)
    sr_nos = {r["sr_no"] for r in results}
    assert 425 in sr_nos
    assert 421 in sr_nos


def test_search_fluticasone_furoate_contains_771():
    """search('fluticasone furoate') contains sr_no 771."""
    items = catalog.load_catalog()
    results = catalog.search("fluticasone furoate", items)
    sr_nos = {r["sr_no"] for r in results}
    assert 771 in sr_nos


def test_no_component_salt_ends_with_noise_words():
    """No component salt in the catalog ends with any of these words: spray, respules, respirator, nasal, drops, solution, eye drops, ophthalmic, opthalmic, paediatric, pediatric."""
    forbidden = [
        "spray", "respules", "respirator", "nasal", "drops", "solution",
        "eye drops", "ophthalmic", "opthalmic", "paediatric", "pediatric"
    ]
    items = catalog.load_catalog()
    offending = []
    for item in items:
        for c in item.get("components", []):
            salt = c.get("salt", "")
            for w in forbidden:
                if salt.endswith(w):
                    offending.append((item.get("sr_no"), salt, w))
    if offending:
        print("Offending salts found:", offending)
    assert len(offending) == 0, f"Found offending salts: {offending}"


def test_no_empty_salt_in_catalog():
    """No component salt in the catalog is an empty string."""
    items = catalog.load_catalog()
    for item in items:
        for c in item.get("components", []):
            salt = c.get("salt", "")
            assert bool(salt and salt.strip()), f"Item {item.get('sr_no')} has empty salt: {c}"

