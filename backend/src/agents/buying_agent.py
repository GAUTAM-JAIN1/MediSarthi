from browser_use import Agent, Browser, ChatGroq, Tools
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

tools = Tools()

# 2 separate agents, one per site, run in PARALLEL via asyncio.gather. Each
# gets its own timeout (per-site, not combined), and each gets its own
# Chrome profile folder — running 2 Chrome instances against the SAME
# --user-data-dir at once causes a lock conflict, so they must use different
# parent folders.
PER_SITE_TIMEOUT_SECONDS = 150

APOLLO_PROFILE_DIR = r"C:\agent_profile_apollo"
ONEMG_PROFILE_DIR = r"C:\agent_profile_1mg"


# ── Final/merged output schema (used by run_comparison + main.py only —
#    NOT passed to the per-site Agent anymore, see note below) ─────────────
#
# CHANGED (D2 compliance fix): the old BestDeal schema only returned a single
# "winning" site, and the agent's task prompt told it to click "Add to cart"
# on the winning site automatically. That directly violated the project's own
# D2 rule (no auto add-to-cart, ever — human-in-the-loop confirmation only).
#
# New approach: the agent ONLY extracts data (price + delivery info) from
# every site, for every medicine. It never clicks "Add to cart" or any
# purchase-path button. The "best" tags (best price / fastest delivery) are
# computed AFTER extraction, in Python, not decided or acted on by the agent.
# Compare.jsx is responsible for showing an "Add to cart" button that simply
# links/redirects the user to the actual pharmacy site — nothing is ever
# added to a cart on the user's behalf.

class PharmacySiteResult(BaseModel):
    site: str = Field(..., description="Pharmacy site name, e.g. '1mg' or 'Apollo Pharmacy'.")
    product_name: str = Field(..., description="Exact product name as shown on the site.")
    price: Optional[float] = Field(None, description="Price in INR. Null if not found/unavailable.")
    quantity: str = Field("", description="Pack size / quantity, e.g. 'strip of 10 tablets'.")
    delivery_info: str = Field("", description="Delivery estimate as shown on the site, e.g. 'Delivery by tomorrow, 2pm'. Empty string if not shown.")
    product_url: str = Field("", description="Direct URL to the product page on this site, so the frontend can link the user there.")
    available: bool = Field(True, description="False if the medicine could not be found on this site at all.")
    notes: str = Field("", description="Any other relevant info shown (offers, discounts) — kept brief.")


class MedicineComparisonResult(BaseModel):
    medicine_name: str = Field(..., description="The medicine name that was searched for.")
    results: List[PharmacySiteResult] = Field(..., description="One result per site checked, for this medicine.")


class ComparisonOutput(BaseModel):
    """Full output for a batch of medicines, across all checked sites. No purchase action is ever taken."""
    medicines: List[MedicineComparisonResult] = Field(..., description="One entry per medicine that was searched for.")


# ── Per-site agent output schema — FLATTENED to avoid a real bug ──────────
#
# CHANGED (bug fix): the previous version used nested Pydantic models here
# (SingleSiteOutput -> SingleSiteMedicineResult -> PharmacySiteResult). When
# use_vision=False forced the agent to fall back to browser-use's internal
# `extract` tool to read page text, that tool tried to validate against this
# nested schema and choked: "Invalid output_schema... Unsupported JSON
# Schema keyword: $defs" — Pydantic generates a $defs/$ref section for any
# nested BaseModel, and browser-use's lightweight extract-tool schema
# checker doesn't resolve $defs. It silently fell back to unstructured
# free-text extraction, which returned garbage (generic page text instead of
# the actual product data) even though the agent WAS on the correct product
# page.
#
# Fix: use a flat List[Dict[str, Any]] instead of a nested model. A dict
# field doesn't generate a named $ref/$defs entry in the JSON schema, so this
# sidesteps the bug entirely — regardless of whether use_vision ends up
# True/False/"auto" later. Validation is looser (we don't get Pydantic field
# validation on each record anymore), so `_run_single_site` defensively
# rebuilds proper PharmacySiteResult objects afterward and skips any
# malformed entries rather than crashing.

class SingleSiteOutput(BaseModel):
    medicines: List[Dict[str, Any]] = Field(
        ...,
        description=(
            "One entry per medicine, for this one site only. Each entry MUST "
            "be a flat object with exactly these keys: medicine_name (string), "
            "site (string), product_name (string), price (number or null), "
            "quantity (string), delivery_info (string), product_url (string), "
            "available (boolean), notes (string)."
        ),
    )


def _build_site_task(site_label: str, site_url: str, medicines: List[str]) -> str:
    return f"""
    You are a price-comparison research assistant. You will look up the following
    medicines on ONE pharmacy website ({site_label}) and report back structured
    data. You will NEVER add anything to a cart, click "Buy Now", click "Add to
    cart", or take any purchase/checkout action of any kind, under any
    circumstances. Your job is to read and report information only.

    Medicines to look up: {medicines}

    Use go_to_url to visit {site_url}

    For EACH medicine in the list:
       - Search for the medicine on this site.
       - Open the first matching product result.
       - Read and record: product name, price, pack quantity, and any delivery
         estimate text shown on the page (e.g. "Delivery by [date]", "Get it by
         tomorrow"). If no delivery estimate is visible, leave it blank — do not
         guess or invent one.
       - Record the product page URL.
       - If the medicine cannot be found on this site at all, mark available
         as false and leave the other fields blank.
       - Go back to the search page before searching for the next medicine.
       - If clicking an element doesn't seem to change the page after a
         couple of seconds, don't keep clicking the same element — try a
         different matching element or re-read the page first.

    IMPORTANT — things you must NEVER do:
       - Never click "Add to cart", "Buy now", "Place order", or any similar
         button.
       - Never proceed past a product page to checkout.
       - Never invent a price, delivery date, or product name that isn't
         actually shown on the page — leave the field blank/null instead.

    Return your findings as structured data: for every medicine, one FLAT
    entry (not nested) with keys: medicine_name, site ("{site_label}"),
    product_name, price, quantity, delivery_info, product_url, available,
    notes.
    """


async def _run_single_site(
    site_label: str,
    site_url: str,
    profile_dir: str,
    medicines: List[str],
) -> List[Dict[str, Any]]:
    """
    Runs one agent against one pharmacy site only. Returns a list of raw
    flat dicts (one per medicine, as the agent reported them) so the caller
    can group them by medicine. Returns an empty list on any failure
    (timeout, no result, malformed output) instead of raising — so a
    problem on ONE site never takes down the other site's result when run
    in parallel via asyncio.gather.
    """
    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

    browser = Browser(
        executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        user_data_dir=profile_dir,
        profile_directory="Default",
        permissions=["geolocation"],
        # Tightened from the original 2.0/2.0/1.0 now that each agent only
        # handles ONE site (less to wait through per agent) and runs in
        # parallel anyway. This part was never the cause of the bugs above —
        # safe to keep.
        minimum_wait_page_load_time=1.0,
        wait_for_network_idle_page_load_time=1.0,
        wait_between_actions=0.5,
    )

    agent = Agent(
        task=_build_site_task(site_label, site_url, medicines),
        llm=llm,
        browser=browser,
        tools=tools,
        output_model_schema=SingleSiteOutput,
        # REVERTED: was False, which pushed the agent onto browser-use's
        # internal `extract` tool (the one that hit the $defs bug above).
        # "auto" lets the agent take a screenshot when it's genuinely unsure
        # what's on the page, without paying the cost of a screenshot on
        # every single step. Safer middle ground than full True or full False.
        use_vision="auto",
        # REVERTED: was True, which skips the "Eval" reasoning step (the
        # agent checking "did my last action actually work?"). That's what
        # let the Apollo agent click the same dead element 5 times in a row
        # before loop-detection kicked in. Eval back on = agent notices a
        # click didn't do anything and tries something else instead.
        # max_actions_per_step is kept — batching up to 3 actions per LLM
        # call is still a safe speed win, unrelated to either bug above.
        max_actions_per_step=3,
    )

    try:
        history = await asyncio.wait_for(agent.run(), timeout=PER_SITE_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        try:
            await browser.close()
        except Exception:
            pass
        print(f"[buying_agent] {site_label} timed out after {PER_SITE_TIMEOUT_SECONDS}s — skipping this site.")
        return []
    except Exception as e:
        try:
            await browser.close()
        except Exception:
            pass
        print(f"[buying_agent] {site_label} failed with an error: {e}")
        return []

    result = history.final_result()
    if not result:
        return []

    structured: SingleSiteOutput = history.structured_output
    if not structured or not structured.medicines:
        return []

    return structured.medicines  # list of flat dicts


def _to_pharmacy_result(raw: Dict[str, Any], fallback_site: str) -> Optional[PharmacySiteResult]:
    """
    Defensively converts one raw flat dict (as returned by the agent) into a
    validated PharmacySiteResult. Returns None (and logs) instead of raising
    if the agent returned something malformed/missing fields — one bad
    record from the LLM shouldn't crash the whole comparison.
    """
    try:
        return PharmacySiteResult(
            site=raw.get("site") or fallback_site,
            product_name=raw.get("product_name") or "",
            price=raw.get("price"),
            quantity=raw.get("quantity") or "",
            delivery_info=raw.get("delivery_info") or "",
            product_url=raw.get("product_url") or "",
            available=raw.get("available", True),
            notes=raw.get("notes") or "",
        )
    except Exception as e:
        print(f"[buying_agent] Skipping a malformed record from {fallback_site}: {e} | raw={raw}")
        return None


async def run_comparison(medicine: List[str]):
    """
    Searches each medicine in `medicine` across 1mg and Apollo Pharmacy in
    PARALLEL (one agent per site) and returns structured price + delivery
    data for every site. Does NOT add anything to any cart — extraction only.
    If one site fails/times out, the other site's results are still returned.
    The caller (main.py) computes 'best price' / 'fastest delivery' tags from
    the returned data; the agents themselves make no purchase decision.
    """
    apollo_coro = _run_single_site(
        "Apollo Pharmacy",
        "https://www.apollopharmacy.in/search-medicines?source=/",
        APOLLO_PROFILE_DIR,
        medicine,
    )
    onemg_coro = _run_single_site(
        "1mg",
        "https://www.1mg.com",
        ONEMG_PROFILE_DIR,
        medicine,
    )

    apollo_raw, onemg_raw = await asyncio.gather(apollo_coro, onemg_coro)

    if not apollo_raw and not onemg_raw:
        # Both sites failed/timed out/returned nothing — nothing to return.
        return None

    # Merge the two single-site outputs back into the original
    # medicine -> [site_result, site_result] shape.
    merged: Dict[str, List[PharmacySiteResult]] = {name: [] for name in medicine}

    for raw in apollo_raw:
        med_name = raw.get("medicine_name", "")
        parsed = _to_pharmacy_result(raw, "Apollo Pharmacy")
        if parsed:
            merged.setdefault(med_name, []).append(parsed)

    for raw in onemg_raw:
        med_name = raw.get("medicine_name", "")
        parsed = _to_pharmacy_result(raw, "1mg")
        if parsed:
            merged.setdefault(med_name, []).append(parsed)

    structured = ComparisonOutput(
        medicines=[
            MedicineComparisonResult(medicine_name=name, results=results)
            for name, results in merged.items()
        ]
    )

    return _attach_best_tags(structured)


def _attach_best_tags(structured: ComparisonOutput) -> dict:
    """
    Takes the raw extracted data and computes, per medicine, which site had
    the best price and which had the fastest/clearest delivery estimate.
    This is plain Python logic — the agent does not decide or act on this,
    it only ever reports raw data. Returns a plain dict ready for the API
    response (so main.py doesn't need to import pydantic models from here).
    """
    output = {"medicines": []}

    for med in structured.medicines:
        available_results = [r for r in med.results if r.available and r.price is not None]

        best_price_site = None
        if available_results:
            best_price_site = min(available_results, key=lambda r: r.price).site

        # "Fastest delivery" is best-effort: we only tag this when at least
        # one site actually showed delivery text. We don't try to parse/compare
        # arbitrary delivery date strings precisely — that's unreliable. If only
        # one site shows any delivery info at all, that site gets the tag.
        sites_with_delivery_info = [r for r in available_results if r.delivery_info.strip()]
        fastest_delivery_site = None
        if len(sites_with_delivery_info) == 1:
            fastest_delivery_site = sites_with_delivery_info[0].site
        # If multiple sites show delivery info, we don't guess which is faster —
        # left as None, and the frontend simply won't show a "fastest" badge for
        # this medicine. Better to show nothing than show a wrong claim.

        med_dict = {
            "medicine_name": med.medicine_name,
            "results": [r.dict() for r in med.results],
            "best_price_site": best_price_site,
            "fastest_delivery_site": fastest_delivery_site,
        }
        output["medicines"].append(med_dict)

    return output