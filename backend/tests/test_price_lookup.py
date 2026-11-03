"""Tests for agents.price_lookup module and catalog-backed price comparison."""

import asyncio
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend/src is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.price_lookup import JANAUSHADHI_SITE, run_comparison
from agents.main import app
from agents.rate_limit import COMPARE_LIMITER


@pytest.fixture
def reset_compare_limiter():
    """Reset rate limiter before and after route test to prevent 429."""
    COMPARE_LIMITER.reset()
    yield
    COMPARE_LIMITER.reset()


def test_run_comparison_shape():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    meds = res.get("medicines", [])
    assert len(meds) == 1
    m = meds[0]
    assert set(m.keys()) == {"medicine_name", "results", "best_price_site", "fastest_delivery_site"}
    results = m["results"]
    assert len(results) > 0

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
        assert r["site"] == JANAUSHADHI_SITE


def test_levothyroxine_synonym():
    res = asyncio.run(run_comparison(["Levothyroxine"]))
    results = res["medicines"][0]["results"]
    assert len(results) > 0


def test_unknown_medicine():
    res = asyncio.run(run_comparison(["Xyzzyqwerty"]))
    m = res["medicines"][0]
    assert m["results"] == []
    assert m["best_price_site"] is None


def test_not_notified_rows():
    res = asyncio.run(run_comparison(["Cetirizine"]))
    results = res["medicines"][0]["results"]
    assert len(results) > 0
    unavail = [r for r in results if not r["available"]]
    assert len(unavail) > 0
    for r in unavail:
        assert r["price"] is None
        assert "price not notified" in r["notes"]


def test_best_price_site_when_available():
    res = asyncio.run(run_comparison(["Paracetamol"]))
    m = res["medicines"][0]
    assert any(r["available"] for r in m["results"])
    assert m["best_price_site"] == JANAUSHADHI_SITE


def test_no_scraping_module():
    assert importlib.util.find_spec("agents.buying_agent") is None
    src_dir = Path(__file__).resolve().parent.parent / "src"
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        assert "browser_use" not in text, f"Found browser_use in {py_file}"
        assert "playwright" not in text, f"Found playwright in {py_file}"


def test_route_medicine_compare_200(reset_compare_limiter):
    client = TestClient(app)
    resp = client.post("/medicine/compare", json={"medicines": ["Paracetamol"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "medicines" in body


def test_openapi_hash_invariant():
    spec_obj = app.openapi()
    spec = json.dumps(spec_obj, sort_keys=True, indent=2)
    computed_hash = hashlib.sha256(spec.encode("utf-8")).hexdigest()
    assert computed_hash == "37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1"

