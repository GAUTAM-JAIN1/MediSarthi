"""Catalog-backed price lookup over the PMBJP list. No network. No scraping."""

from typing import Any, Dict, List, Optional

from agents import catalog

JANAUSHADHI_SITE = "PMBJP Jan Aushadhi"
MAX_RESULTS_PER_MEDICINE = 10


async def run_comparison(medicines: List[str]) -> Dict[str, Any]:
    """Catalog-backed comparison returning PMBJP Jan Aushadhi prices."""
    items = catalog.load_catalog()
    medicines_output: List[Dict[str, Any]] = []

    for raw in medicines:
        name = (raw or "").strip()
        if not name:
            continue

        hits = catalog.search(name, items)[:MAX_RESULTS_PER_MEDICINE]
        results: List[Dict[str, Any]] = []

        for h in hits:
            available = h.get("price_status") == "listed"
            notes = f"{h.get('dosage_form', '')} | list dated {h.get('source_date', '')}"
            if h.get("is_combination"):
                notes += " | combination"
            if h.get("is_concentration"):
                notes += " | concentration (mg/ml)"
            if not available:
                notes += " | price not notified"

            result_entry = {
                "site": JANAUSHADHI_SITE,
                "product_name": h.get("name_raw", ""),
                "price": h.get("mrp"),
                "quantity": h.get("unit_size_raw", ""),
                "delivery_info": "",
                "product_url": "",
                "available": available,
                "notes": notes,
            }
            results.append(result_entry)

        best_price_site: Optional[str] = (
            JANAUSHADHI_SITE if any(r["available"] for r in results) else None
        )

        medicines_output.append(
            {
                "medicine_name": name,
                "results": results,
                "best_price_site": best_price_site,
                "fastest_delivery_site": None,
            }
        )

    return {"medicines": medicines_output}

