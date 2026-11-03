import csv
import json
import hashlib
import re
from collections import defaultdict, Counter
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from agents import catalog


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_import():
    csv_path = BASE_DIR / "data" / "janaushadhi" / "PMBJP_Product_List_2026-11-02.csv"
    non_med_path = BASE_DIR / "data" / "catalog" / "non_medicine_groups.json"
    output_json = BASE_DIR / "data" / "catalog" / "janaushadhi.json"
    report_json = BASE_DIR / "data" / "catalog" / "import_report.json"

    input_sha256 = compute_sha256(csv_path)

    with open(non_med_path, "r", encoding="utf-8") as f:
        non_medicine_groups = set(json.load(f))

    raw_rows = []
    groups_by_lower = defaultdict(Counter)

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)
            grp = row["Group Name"].strip()
            groups_by_lower[grp.lower()][grp] += 1

    canonical_group_map = {}
    group_case_variants = []
    for low, counter in sorted(groups_by_lower.items()):
        most_common = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
        canonical = most_common[0][0]
        canonical_group_map[low] = canonical
        if len(counter) > 1:
            group_case_variants.append({
                "canonical": canonical,
                "variants": sorted(list(counter.keys()))
            })

    items = []
    slash_strength_rows = 0
    slash_mismatch_rows = 0

    for row in raw_rows:
        drug_code = row["Drug Code"].strip()
        sr_no = int(row["Sr No"].strip())
        name_raw = row["Generic Name"].strip()
        name_clean = catalog.normalize_text(name_raw)

        m = catalog.SLASH_STRENGTH_PATTERN.search(name_clean)
        if m:
            slash_strength_rows += 1

        components = catalog.parse_components(name_raw)
        row_parse_ok = bool(components) and all(c.get("parse_ok", False) for c in components)

        if m:
            # Check if slash mismatch occurred:
            # If m matched, but row_parse_ok is False, it was a mismatch between salt count and numbers count
            if not row_parse_ok:
                slash_mismatch_rows += 1

        unit_size_raw = row["Unit Size"].strip()
        dosage_form = catalog.dosage_form(name_raw, unit_size_raw)
        pack_count = catalog.pack_count(unit_size_raw)

        mrp_str = row["MRP"].strip()
        try:
            mrp_val = float(mrp_str)
        except ValueError:
            mrp_val = 0.0

        if mrp_val > 0.0:
            mrp = mrp_val
            price_status = "listed"
        else:
            mrp = None
            price_status = "not_notified"

        price_per_unit = catalog.per_unit_price(mrp, pack_count)
        group_canonical = canonical_group_map[row["Group Name"].strip().lower()]
        is_medicine = group_canonical not in non_medicine_groups
        is_combination = len(components) > 1
        is_concentration = catalog.CONCENTRATION_RX.search(name_clean) is not None

        item = {
            "drug_code": drug_code,
            "sr_no": sr_no,
            "name_raw": name_raw,
            "name_clean": name_clean,
            "components": components,
            "parse_ok": row_parse_ok,
            "dosage_form": dosage_form,
            "unit_size_raw": unit_size_raw,
            "pack_count": pack_count,
            "mrp": mrp,
            "price_status": price_status,
            "price_per_unit": price_per_unit,
            "group_canonical": group_canonical,
            "is_medicine": is_medicine,
            "is_combination": is_combination,
            "is_concentration": is_concentration,
            "source": "PMBJP Product List",
            "source_date": "2026-11-02",
        }
        items.append(item)

    items.sort(key=lambda x: x["sr_no"])

    drug_codes = [item["drug_code"] for item in items]
    if len(set(drug_codes)) != len(items):
        raise ValueError(
            f"Duplicate drug codes found! Unique: {len(set(drug_codes))}, Total: {len(items)}"
        )

    pairs = defaultdict(list)
    for item in items:
        pairs[(item["name_clean"], item["unit_size_raw"])].append(item["drug_code"])

    duplicate_name_unit_pairs = []
    for (name_clean, unit_raw), codes in sorted(pairs.items()):
        if len(codes) > 1:
            duplicate_name_unit_pairs.append({
                "name_clean": name_clean,
                "unit_size_raw": unit_raw,
                "drug_codes": codes,
            })

    total_rows = len(items)
    unique_drug_codes = len(set(drug_codes))
    zero_mrp_rows = sum(1 for x in items if x["price_status"] == "not_notified")
    no_strength_rows = sum(1 for x in items if not x["parse_ok"])
    combination_rows = sum(1 for x in items if x["is_combination"])
    concentration_rows = sum(1 for x in items if x["is_concentration"])
    pack_count_present_rows = sum(1 for x in items if x["pack_count"] is not None)
    non_medicine_rows = sum(1 for x in items if not x["is_medicine"])

    output_dir = output_json.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    json_bytes = (json.dumps(items, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(output_json, "wb") as f:
        f.write(json_bytes)

    output_sha256 = hashlib.sha256(json_bytes).hexdigest()

    report = {
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "total_rows": total_rows,
        "unique_drug_codes": unique_drug_codes,
        "zero_mrp_rows": zero_mrp_rows,
        "no_strength_rows": no_strength_rows,
        "slash_strength_rows": slash_strength_rows,
        "slash_mismatch_rows": slash_mismatch_rows,
        "combination_rows": combination_rows,
        "concentration_rows": concentration_rows,
        "pack_count_present_rows": pack_count_present_rows,
        "non_medicine_rows": non_medicine_rows,
        "group_case_variants": group_case_variants,
        "duplicate_name_unit_pairs": duplicate_name_unit_pairs,
    }

    report_bytes = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    with open(report_json, "wb") as f:
        f.write(report_bytes)

    print(f"Import completed successfully.")
    print(f"Total rows: {total_rows}")
    print(f"Unique drug codes: {unique_drug_codes}")
    print(f"Zero MRP rows: {zero_mrp_rows}")
    print(f"No strength rows: {no_strength_rows}")
    print(f"Slash strength rows: {slash_strength_rows}")
    print(f"Slash mismatch rows: {slash_mismatch_rows}")
    print(f"Combination rows: {combination_rows}")
    print(f"Concentration rows: {concentration_rows}")
    print(f"Pack count present rows: {pack_count_present_rows}")
    print(f"Non-medicine rows: {non_medicine_rows}")
    print(f"Output SHA256: {output_sha256}")


if __name__ == "__main__":
    run_import()
