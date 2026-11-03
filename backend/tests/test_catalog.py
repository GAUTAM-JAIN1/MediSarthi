import json
import hashlib
from pathlib import Path
import socket
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agents import catalog


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Ensure catalog code makes zero network calls."""
    def _guarded(*args, **kwargs):
        raise RuntimeError("Network calls are forbidden during catalog tests")
    monkeypatch.setattr(socket, "socket", _guarded)


def test_row_count_and_unique_codes():
    catalog.load_catalog.cache_clear()
    items = catalog.load_catalog()
    assert len(items) == 2445
    codes = [item["drug_code"] for item in items]
    assert len(set(codes)) == 2445


def test_zero_mrp_rows_are_null():
    items = catalog.load_catalog()
    not_notified = [item for item in items if item["price_status"] == "not_notified"]
    assert len(not_notified) == 345
    for item in not_notified:
        assert item["mrp"] is None
        assert item["price_per_unit"] is None


def test_paracetamol_650_per_unit():
    items = catalog.load_catalog()
    sr398 = next((item for item in items if item["sr_no"] == 398), None)
    assert sr398 is not None
    assert sr398["mrp"] == 15.47
    assert sr398["pack_count"] == 15
    assert sr398["price_per_unit"] == 1.03
    assert sr398["dosage_form"] == "Tablet"


def test_levothyroxine_synonym_search():
    items = catalog.load_catalog()
    results = catalog.search("levothyroxine", items)
    assert len(results) >= 8
    for item in results:
        assert any(c.get("salt") == "levothyroxine" for c in item.get("components", []))


def test_duplicate_name_different_codes():
    items = catalog.load_catalog()
    sr1042 = next((item for item in items if item["sr_no"] == 1042), None)
    sr1295 = next((item for item in items if item["sr_no"] == 1295), None)
    assert sr1042 is not None
    assert sr1295 is not None
    assert sr1042["drug_code"] != sr1295["drug_code"]
    assert sr1042["mrp"] != sr1295["mrp"]


def test_group_canonicalization():
    items = catalog.load_catalog()
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    expected_canonical = next(
        g["canonical"] for g in report["group_case_variants"] if g["canonical"].lower() == "anti-fungal"
    )

    anti_fungals = [item["group_canonical"] for item in items if item["group_canonical"].lower() == "anti-fungal"]
    assert len(anti_fungals) > 0
    distinct_spellings = set(anti_fungals)
    assert len(distinct_spellings) == 1
    assert distinct_spellings == {expected_canonical}


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("Paracetamol Tablets IP 650 mg", [("paracetamol", 650.0, "mg")]),
        ("Amoxycillin 500mg and Potassium Clavulanate 125mg Tablets IP", [("amoxicillin", 500.0, "mg"), ("clavulanic acid", 125.0, "mg")]),
        ("Thyroxine Sodium Tablets IP 100 mcg", [("levothyroxine", 100.0, "mcg")]),
        ("Metformin Hydrochloride Sustained Release Tablets IP 1000 mg", [("metformin", 1000.0, "mg")]),
        ("Atorvastatin 10mg and Clopidogrel 75mg Capsules", [("atorvastatin", 10.0, "mg"), ("clopidogrel", 75.0, "mg")]),
        ("Glimepiride Tablets  IP 3mg", [("glimepiride", 3.0, "mg")]),
        ("Losartan Potassium 50mg and Hydrochlorothiazide 12.5mg Tabelts IP", [("losartan potassium", 50.0, "mg"), ("hydrochlorothiazide", 12.5, "mg")]),
        ("S(-)Amlodipine Tablets IP 2.5 mg", [("levamlodipine", 2.5, "mg")]),
    ]
)
def test_parse_components_cases(raw_name, expected):
    comps = catalog.parse_components(raw_name)
    actual = [(c["salt"], c["strength"], c["unit"]) for c in comps]
    assert actual == expected


@pytest.mark.parametrize(
    "unit_size, expected",
    [
        ("10's", 10),
        ("4'S", 4),
        ("1’s Sachet", 1),
        ("100's in Bottle", 100),
        ("100 ml", None),
        ("Vial & Wfi", None),
        ("30g", None),
    ]
)
def test_pack_count_cases(unit_size, expected):
    assert catalog.pack_count(unit_size) == expected


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        ("Ondansetron Injection IP 2mg per ml", "Injection"),
        ("Pantoprazole Gastro Resistant Tablets IP 40 mg", "Tablet"),
        ("Pilocarpine Eye Drops IP 2% W/V", "Drops"),
    ]
)
def test_dosage_form_cases(raw_name, expected):
    assert catalog.dosage_form(raw_name) == expected


def test_per_unit_price_rules():
    assert catalog.per_unit_price(0, 10) is None
    assert catalog.per_unit_price(15.47, None) is None
    assert catalog.per_unit_price(15.47, 15) == 1.03


def test_importer_deterministic():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "janaushadhi.json"

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    h = hashlib.sha256()
    with open(catalog_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    current_hash = h.hexdigest()

    assert report["output_sha256"] == current_hash


@pytest.mark.parametrize(
    "raw_name, expected",
    [
        (
            "Atenolol + Chlorthalidone Tablet (25/12.5 Mg)",
            [("atenolol", 25.0, "mg", True), ("chlorthalidone", 12.5, "mg", True)],
        ),
        (
            "Gliclazide + Pioglitazone + Metformin Tablet (30/15/500 Mg)",
            [("gliclazide", 30.0, "mg", True), ("pioglitazone", 15.0, "mg", True), ("metformin", 500.0, "mg", True)],
        ),
        (
            "Amlodipine + Enalapril Tablet (5/5 Mg)",
            [("amlodipine", 5.0, "mg", True), ("enalapril", 5.0, "mg", True)],
        ),
        (
            "Paracetamol Tablets IP 650 mg",
            [("paracetamol", 650.0, "mg", True)],
        ),
    ],
)
def test_parse_components_slash_and_base_cases(raw_name, expected):
    comps = catalog.parse_components(raw_name)
    actual = [(c["salt"], c["strength"], c["unit"], c["parse_ok"]) for c in comps]
    assert actual == expected


def test_parse_components_no_strength_unflavored_base():
    comps = catalog.parse_components("Syrup of Iron and Folic Acid in a flavoured Base")
    assert all(c["parse_ok"] is False for c in comps)


def test_importer_row_2014_slash_strength():
    items = catalog.load_catalog()
    sr2014 = next((item for item in items if item["sr_no"] == 2014), None)
    assert sr2014 is not None
    assert len(sr2014["components"]) == 2
    assert sr2014["components"][0]["strength"] == 25.0
    assert sr2014["components"][1]["strength"] == 12.5
    assert sr2014["components"][0]["parse_ok"] is True
    assert sr2014["components"][1]["parse_ok"] is True
    assert sr2014["parse_ok"] is True


def test_search_exclusion_amlodipine():
    items = catalog.load_catalog()
    results = catalog.search("amlodipine", items)
    assert not any(
        any(c.get("salt") == "levamlodipine" for c in item.get("components", []))
        for item in results
    )


def test_search_fallback_levamlodipine():
    items = catalog.load_catalog()
    results = catalog.search("levamlodipine", items)
    assert len(results) >= 1


def test_report_keys_and_values():
    report_path = Path(__file__).resolve().parent.parent / "data" / "catalog" / "import_report.json"
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    assert "no_strength_rows" in report
    assert "slash_strength_rows" in report
    assert "slash_mismatch_rows" in report
    assert "parse_failed_rows" not in report
    assert report["slash_strength_rows"] == 41
    assert report["slash_mismatch_rows"] == 0
