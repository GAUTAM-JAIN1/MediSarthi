# PROMPT 08e DELIVERABLE DUMP

## 1. HEADER
- **Title:** Prompt 08e Deliverable Dump — Eye-Drop, Nasal and Solution Noise Words, Deliberate Catalog Hash Change, Latanoprost Single-Ingredient Drops
- **Date:** 3 November 2026
- **Prompt:** 08e
- **Commit HEAD SHA:** `1151654` (branch `phase-1-catalog`)
- **Execution Duration:** ~12 minutes
- **Final Status:** CLEAN

---

## 2. PRE-FLIGHT
- **Verification `Project-docs\dumps\P08d_dump.md` exists:** Confirmed (`True`).
- **Active Python Processes:** Confirmed 0 active Python processes.
- **Catalog Hash Before Edit:** `7662d5a8a0330cd57d3dd7b09cd3ff18dc7291ce47079c65ff388292ae422e08`
- **Commit HEAD SHA and Branch:** `1151654` on branch `phase-1-catalog`.

---

## 3. BASELINE
- **Pytest Summary Before Changes:** 168 passed, 1 failed in 38.07s.
- **Failing Test:** `tests/test_liquid_policy.py::test_run_comparison_latanoprost`
- **Route Count:** 43 operations.
- **OpenAPI In-Memory LF Canonical SHA256:** `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`

---

## 4. REPRODUCTION
Output of Step 2 script (`python -`):
```text
Item 1970 component salts: ['latanoprost eye drops']
Item 1810 component salts: ['latanoprost', 'timolol maleate']
search('latanoprost') result sr_nos: [1810]
First result sr_no: 1810
```

---

## 5. CODE CHANGES
### Noise Words Added to `_WORDS_TO_REMOVE` in `backend/src/agents/catalog.py`:
1. `"eye drops"`
2. `"eye drop"`
3. `"ear drops"`
4. `"ear drop"`
5. `"drops"`
6. `"nasal"`
7. `"ophthalmic"`
8. `"opthalmic"`
9. `"solution"`

### COMPLETE File Content of `backend/src/agents/catalog.py`:
```python
import os
import re
import json
import functools
from typing import Optional, List, Dict, Any, Tuple

_SYNONYMS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog", "synonyms.json")
)
_JANAUSHADHI_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog", "janaushadhi.json")
)

SLASH_STRENGTH_PATTERN = re.compile(
    r"\(\s*(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)+)\s*(mg|mcg|g|iu|%|ml)\s*\)",
    re.IGNORECASE,
)

_WORDS_TO_REMOVE = [
    "gastro-resistant", "gastro resistant", "enteric coated",
    "gastro", "resistant", "enteric", "coated",
    "tablets", "tablet", "tab", "ip", "capsules", "capsule",
    "injection", "syrup", "suspension", "gel", "cream",
    "sr", "er", "prolonged", "sustained", "release",
    "delayed", "modified", "extended", "dispersible", "oral", "granules",
    "paediatric", "pediatric",
    "eye drops", "eye drop", "ear drops", "ear drop", "drops", "nasal", "ophthalmic", "opthalmic", "solution",
]
_REMOVE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in sorted(_WORDS_TO_REMOVE, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)
_NUM_UNIT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|iu|%|ml)", re.IGNORECASE)
_SPLIT_PATTERN = re.compile(r"\s+and\s+|,|&|\+", re.IGNORECASE)
_PACK_RE = re.compile(r"^\s*(\d+)\s*(?:['’‘\ufffd]\s*s\b|s\b|['’‘\ufffd]\b)", re.IGNORECASE)

_DOSAGE_FORMS = [
    ("Injection", re.compile(r"injection|inection|infusion", re.IGNORECASE)),
    ("Liquid", re.compile(r"syrup|suspension|oral solution|solution", re.IGNORECASE)),
    ("Drops", re.compile(r"drops|ophthalmic|eye drop|ear drop", re.IGNORECASE)),
    ("Gel", re.compile(r"\bgel\b", re.IGNORECASE)),
    ("Topical", re.compile(r"cream|ointment|lotion|spray|patch", re.IGNORECASE)),
    ("Capsule", re.compile(r"capsule", re.IGNORECASE)),
    ("Tablet", re.compile(r"tablet|tabelts|\btab\b", re.IGNORECASE)),
    ("Powder", re.compile(r"powder|sachet|granule", re.IGNORECASE)),
]


@functools.lru_cache(maxsize=1)
def _load_synonyms() -> Dict[str, str]:
    if os.path.exists(_SYNONYMS_FILE):
        with open(_SYNONYMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\s*\(\s*-\s*\)\s*", "(-)", s)
    s = s.replace("tabelts", "tablets")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def canonical_salt(name: str) -> str:
    norm = normalize_text(name)
    synonyms = _load_synonyms()
    return synonyms.get(norm, norm)


def parse_components(generic_name: str) -> List[Dict[str, Any]]:
    norm_name = normalize_text(generic_name)
    m = SLASH_STRENGTH_PATTERN.search(norm_name)
    if m:
        nums = [float(x) for x in re.split(r"\s*/\s*", m.group(1))]
        unit = m.group(2).lower()
        norm_name = norm_name[:m.start()] + " " + norm_name[m.end():]
        norm_name = re.sub(r"\s+", " ", norm_name).strip()
    else:
        nums = None
        unit = None

    parts = _SPLIT_PATTERN.split(norm_name)
    raw_salts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        pm = _NUM_UNIT_PATTERN.search(part)
        if pm:
            salt_raw = part[:pm.start()]
        else:
            salt_raw = part

        salt_clean = _REMOVE_PATTERN.sub(" ", salt_raw)
        salt_clean = re.sub(r"\s+\([^)]*\)\s*$", "", salt_clean)
        salt_clean = re.sub(r"\s*\([^\)]*$", "", salt_clean)
        salt_clean = normalize_text(salt_clean)
        if salt_clean:
            salt = canonical_salt(salt_clean)
            raw_salts.append((salt, pm))

    if not raw_salts:
        return [{
            "salt": canonical_salt(generic_name),
            "strength": None,
            "unit": None,
            "parse_ok": False,
        }]

    components = []
    if nums is not None:
        if len(raw_salts) == len(nums):
            for i, (salt, _) in enumerate(raw_salts):
                components.append({
                    "salt": salt,
                    "strength": nums[i],
                    "unit": unit,
                    "parse_ok": True,
                })
        else:
            for salt, _ in raw_salts:
                components.append({
                    "salt": salt,
                    "strength": None,
                    "unit": None,
                    "parse_ok": False,
                })
    else:
        for salt, pm in raw_salts:
            if pm:
                s_val = float(pm.group(1))
                u_val = pm.group(2).lower()
                ok = True
            else:
                s_val = None
                u_val = None
                ok = False
            components.append({
                "salt": salt,
                "strength": s_val,
                "unit": u_val,
                "parse_ok": ok,
            })

    return components


def dosage_form(generic_name: str, unit_size: str = "") -> str:
    generic_name = generic_name or ""
    unit_size = unit_size or ""
    for name, pattern in _DOSAGE_FORMS:
        if pattern.search(generic_name):
            return name
    for name, pattern in _DOSAGE_FORMS:
        if pattern.search(unit_size):
            return name
    return "Other"


def pack_count(unit_size: str) -> Optional[int]:
    if not unit_size:
        return None
    m = _PACK_RE.search(unit_size)
    if m:
        return int(m.group(1))
    return None


def per_unit_price(mrp: Optional[float], pack: Optional[int]) -> Optional[float]:
    if mrp is None or pack is None or mrp == 0:
        return None
    return round(mrp / pack, 2)


@functools.lru_cache(maxsize=1)
def load_catalog(path: Optional[str] = None) -> List[Dict[str, Any]]:
    catalog_path = path or _JANAUSHADHI_FILE
    with open(catalog_path, "r", encoding="utf-8") as f:
        return json.load(f)


_QUERY_PATTERN = re.compile(
    r"^(?P<name>.+?)\s+(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|iu|%|ml)?$",
    re.IGNORECASE,
)


def parse_query(q: str) -> Tuple[str, Optional[float], Optional[str]]:
    norm = normalize_text(q)
    m = _QUERY_PATTERN.match(norm)
    if m:
        name = m.group("name")
        num = float(m.group("num"))
        unit = m.group("unit").lower() if m.group("unit") else None
        return (canonical_salt(name), num, unit)
    return (canonical_salt(norm), None, None)


CONCENTRATION_RX = re.compile(
    r"\d\s*(mg|mcg|g|iu|%)\s*(/|per)\s*\d*\.?\d*\s*(ml|l)\b",
    re.IGNORECASE,
)


def is_liquid_form(item: Dict[str, Any]) -> bool:
    return bool(item.get("is_concentration")) or item.get("dosage_form") in {"Liquid", "Drops"}


def is_concentration_row(item: Dict[str, Any]) -> bool:
    return is_liquid_form(item)


def _form_rank(item: Dict[str, Any]) -> int:
    return 1 if is_liquid_form(item) else 0


def search(query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Search catalog items for query.
    Liquids and drops are included; solid forms rank first; no silent fallback when a unit is given.
    If strength is specified:
      - Returns exact salt and strength matches.
      - If no exact match and unit is None, falls back to items whose name_clean
        contains the full normalized query (including number).
      - If unit is specified, never falls back.
    If strength is not specified, returns exact salt matches if any, or falls back to name_clean substring.
    Results are sorted by form rank (solid forms first), single-ingredient first,
    price_per_unit ascending (None last), and drug_code.
    """
    name, strength, unit = parse_query(query)
    exact = [item for item in items if any(c.get("salt") == name for c in item.get("components", []))]

    if strength is not None:
        matches = [
            item for item in exact
            if any(
                c.get("salt") == name
                and c.get("strength") == strength
                and (unit is None or c.get("unit") == unit)
                for c in item.get("components", [])
            )
        ]
        if not matches and unit is None:
            full_norm = normalize_text(query)
            matches = [
                item for item in items
                if full_norm in item.get("name_clean", "")
            ]
    else:
        matches = exact if exact else [item for item in items if name in item.get("name_clean", "")]

    matches.sort(
        key=lambda item: (
            _form_rank(item),
            item.get("is_combination", False),
            item.get("price_per_unit") is None,
            item.get("price_per_unit") or 0.0,
            item.get("drug_code", ""),
        )
    )
    return matches
```

---

## 6. IMPORTER VERIFICATION
### Run 1 Report Summary Tail:
```text
=== Import Report Summary ===
total_rows: 2445
zero_mrp_rows: 345
no_strength_rows: 382
slash_strength_rows: 41
slash_mismatch_rows: 0
combination_rows: 878
concentration_rows: 133
pack_count_present_rows: 1730
non_medicine_rows: 350
SHA256 (janaushadhi.json): 878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3
Import completed successfully.
```

### Run 2 Report Summary Tail:
```text
=== Import Report Summary ===
total_rows: 2445
zero_mrp_rows: 345
no_strength_rows: 382
slash_strength_rows: 41
slash_mismatch_rows: 0
combination_rows: 878
concentration_rows: 133
pack_count_present_rows: 1730
non_medicine_rows: 350
SHA256 (janaushadhi.json): 878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3
Import completed successfully.
```

### Reproducibility Verification:
- **Run 1 SHA256:** `878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3`
- **Run 2 SHA256:** `878324ce78166edd10ebe11ae2edcc0e229e7470adb64ce18b9cb8820c6288c3`
- Hashes match exactly across independent clean-state importer runs.

### Component Salt Changes Between P08d and P08e Catalog:
- **Total changed catalog items:** Exactly 61 items.
- **First 10 changed items:**
  1. `sr_no 113: Povidone-Iodine Solution IP 10 % w/v | old salt: ['povidone-iodine solution'] | new salt: ['povidone-iodine']`
  2. `sr_no 114: Povidone-Iodine Solution IP 5 % w/v | old salt: ['povidone-iodine solution'] | new salt: ['povidone-iodine']`
  3. `sr_no 115: Povidone Iodine Solution 7.5% w/v | old salt: ['povidone iodine solution'] | new salt: ['povidone iodine']`
  4. `sr_no 158: Lactulose Solution IP 10g per 15ml | old salt: ['lactulose solution'] | new salt: ['lactulose']`
  5. `sr_no 266: Carboxymethylcellulose Sodium Eye Drops IP 0.5% w/v | old salt: ['carboxymethylcellulose sodium eye drops'] | new salt: ['carboxymethylcellulose sodium']`
  6. `sr_no 267: Ciprofloxacin Eye Drops IP 0.3% w/v | old salt: ['ciprofloxacin eye drops'] | new salt: ['ciprofloxacin']`
  7. `sr_no 268: Gentamicin Eye Drops IP 0.3% w/v | old salt: ['gentamicin eye drops'] | new salt: ['gentamicin']`
  8. `sr_no 269: Xylometazoline Nasal Drops IP 0.1%w/v | old salt: ['xylometazoline nasal drops'] | new salt: ['xylometazoline']`
  9. `sr_no 419: Saline Nasal Drops (Sodium Chloride 0.65% w/v) | old salt: ['saline nasal drops'] | new salt: ['saline']`
  10. `sr_no 425: Fluticasone Propionate Nasal Spray IP 50 mcg | old salt: ['fluticasone propionate nasal spray'] | new salt: ['fluticasone propionate spray']`

- **Empty Salt String Verification:** 0 component salts in the catalog are empty strings.

---

## 7. NEW TESTS
### COMPLETE File Content of `backend/tests/test_eye_drops.py`:
```python
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
```

### Pytest Output (`test_eye_drops.py`):
```text
.......                                                                  [100%]
7 passed in 0.12s
```

### Pytest Output (`test_liquid_policy.py`):
```text
.......                                                                  [100%]
7 passed in 0.07s
```
*(All 7 tests pass without edits, including `test_run_comparison_latanoprost`)*

---

## 8. FULL VERIFICATION
### Step 6a: Full Test Suite Output
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.5.0
rootdir: C:\Users\gauta\OneDrive\Desktop\MediSarthi\MediSarthi\backend
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.2, cov-6.0.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop=None
collected 176 items

tests/test_agents.py .................................                  [ 18%]
tests/test_api.py ...................                                   [ 29%]
tests/test_auth.py ...........                                          [ 35%]
tests/test_catalog_import.py ..........                                 [ 41%]
tests/test_compare.py .......                                           [ 45%]
tests/test_concentration_guard.py ...............                       [ 53%]
tests/test_conversations.py .                                           [ 54%]
tests/test_eye_drops.py .......                                         [ 58%]
tests/test_liquid_policy.py .......                                     [ 62%]
tests/test_ocr.py .........                                             [ 67%]
tests/test_prescriptions.py ..............                              [ 75%]
tests/test_profile.py .                                                 [ 76%]
tests/test_request_context.py ..                                        [ 77%]
tests/test_router_coverage.py ....................................      [ 97%]
tests/test_search_quality.py .....                                      [100%]

======================== 176 passed, 2 warnings in 27.13s =====================
```

### Step 6b: Verification Script Output Verbatim
```text
Item 1970 component salts: ['latanoprost']
Item 1810 component salts: ['latanoprost', 'timolol maleate']
search('latanoprost') result sr_nos: [1970, 1810]
First result sr_no: 1970
```

### Step 6c: Subprocess Import Check
```text
IMPORT_OK
```

### Step 6d: Route Count & OpenAPI Hash
- **Operations Count:** 43
- **OpenAPI In-Memory LF Canonical SHA256:** `37e7e6f856a75e0a22c7397aa798e9a19bebd22c4227a7c4e87f1382c5f668d1`

### Step 6e: Zero Occurrences of `browser_use` or `playwright` in `backend/src`:
- Confirmed 0 occurrences.

### Step 6f: Live Server Comparison Output Verbatim
- **Endpoint:** `POST /medicine/compare`
- **Payload:** `{"medicines": ["Latanoprost", "Xylometazoline"]}`
- **Timing:** `163.3568 ms` (~163.36 ms; faster than P08d: 194.92 ms)
- **First 2 Results Captured Verbatim:**
```text
=== Medicine: Latanoprost ===
Result 0:
  product_name: Latanoprost Eye Drops IP 0.005% w/v (50mcg per ml)
  generic_name: Latanoprost Eye Drops IP 0.005% w/v (50mcg per ml)
  dosage_form: Drops
  pack_size: 1's
  unit_price: 61.0
  notes: Drops | list dated 02/11/2026 | concentration (mg/ml) | drops: follow the label. Not a tablet strength.

Result 1:
  product_name: Latanoprost and Timolol Solution
  generic_name: Latanoprost and Timolol Solution
  dosage_form: Liquid
  pack_size: 1's
  unit_price: 154.0
  notes: Liquid | list dated 02/11/2026 | combination | liquid: strength is per volume. Dose is in ml, not tablets. Confirm the dose with a doctor or pharmacist.

=== Medicine: Xylometazoline ===
Result 0:
  product_name: Xylometazoline Nasal Drops IP 0.1%w/v
  generic_name: Xylometazoline Nasal Drops IP 0.1%w/v
  dosage_form: Drops
  pack_size: 1's
  unit_price: 18.0
  notes: Drops | list dated 02/11/2026 | concentration (mg/ml) | drops: follow the label. Not a tablet strength.

Result 1:
  product_name: Xylometazoline Nasal Drops IP 0.05% w/v
  generic_name: Xylometazoline Nasal Drops IP 0.05% w/v
  dosage_form: Drops
  pack_size: 1's
  unit_price: 17.5
  notes: Drops | list dated 02/11/2026 | concentration (mg/ml) | drops: follow the label. Not a tablet strength.
```

### Step 6g: `git status --short` Verbatim
```text
 M backend/data/catalog/import_report.json
 M backend/data/catalog/janaushadhi.json
 M backend/src/agents/catalog.py
 M backend/src/agents/price_lookup.py
 M backend/tests/test_concentration_guard.py
?? backend/tests/test_eye_drops.py
?? backend/tests/test_liquid_policy.py
?? local-changes.patch
```

---

## 9. FILE LIFECYCLE
| File Path | Purpose | Deletion Status |
|---|---|---|
| `backend/pytest_out.txt` | Baseline test suite output capture | Confirmed Deleted |
| `backend/pytest_eye.txt` | New test file pytest capture | Confirmed Deleted |
| `backend/pytest_all.txt` | Full test suite verification output | Confirmed Deleted |
| `backend/import_run1.txt` | Importer run 1 stdout capture | Confirmed Deleted |
| `backend/import_run2.txt` | Importer run 2 stdout capture | Confirmed Deleted |
| `backend/data/catalog/janaushadhi.p08d.json` | Temporary backup of P08d catalog | Confirmed Deleted |

---

## 10. OPEN ITEMS AND DEFERRED WORK
- **Leftover Noise Words Deferred:**
  - `"respirator"` (sr_no 431) and `"enzyme"` (sr_no 483). Neither affects search matching or component salt resolution for any active search target; both deferred until concrete issues arise.
- **Safety Copy Clinical Review (Carried Over):**
  - Clinical safety copy added in `price_lookup.py` requires clinician/pharmacist validation before public deployment.
- **Status of P08d Blocker:** Fully RESOLVED.

---

## 11. BLOCKERS
None. All 176 tests pass cleanly. Route count, OpenAPI hash, catalog reproducibility, and endpoint behavior are fully verified.

