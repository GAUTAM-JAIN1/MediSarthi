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
    "spray", "respules", "respirator",
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
