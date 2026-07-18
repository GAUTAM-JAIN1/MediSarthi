from browser_use import Agent, Browser, ChatGroq, Tools
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

tools = Tools()

# ── Sequential vs parallel toggle ──────────────────────────────────────────
#
# FIX (real root cause of the 502s, not the earlier timeout bump): the repeated
# "LLM call timed out after 75 seconds" errors in the logs are a HARDCODED
# internal timeout inside browser-use itself (not PER_SITE_TIMEOUT_SECONDS
# below, which only bounds the whole agent.run() call from the outside).
# When that internal call times out, browser-use retries the SAME step up to
# 6 times ("Result failed 1/6" ... "6/6") before giving up on that step —
# so one slow LLM response can burn several minutes on its own, regardless
# of how high we set our own outer timeout. Bumping PER_SITE_TIMEOUT_SECONDS
# alone (150 -> 220) did NOT fix this, confirmed by the latest log: both
# agents still hit repeated 75s internal timeouts and both still got killed
# by the outer 220s limit before finishing all 3 medicines.
#
# The two agents were running in PARALLEL (asyncio.gather), each firing its
# own LLM call every step, both against the SAME Groq API key at the same
# time. The timing in the log shows Apollo's step-8 75s-timeout landing
# right as 1mg's step-5 extract call was also in flight — consistent with
# Groq-side contention/rate-limiting under concurrent load, which is the
# most likely reason individual calls that are normally fast (llama-4-scout)
# occasionally stall past 75s.
#
# Fix: run the two site-agents SEQUENTIALLY instead of in parallel, so only
# one is ever calling Groq at a time. Slower wall-clock overall (roughly
# apollo_time + onemg_time instead of max(apollo_time, onemg_time)), but
# removes the contention that's currently causing near-100% failure. Kept
# as a simple boolean toggle — flip back to False once Groq's rate limits
# are less of a bottleneck (e.g. a paid tier, or a different provider) to
# get the speed back.
RUN_SEQUENTIALLY = True

# Outer safety-net timeout per site. With sequential execution there's no
# contention forcing repeated 75s internal retries anymore, so this should
# rarely need to fire — kept generous (240s) as a genuine worst-case ceiling
# (page load issues, a truly stuck element, etc), not as the primary fix.
PER_SITE_TIMEOUT_SECONDS = 240

# Only used on the (currently disabled) parallel path — spreads the two
# agents' first LLM calls apart in time. Irrelevant while RUN_SEQUENTIALLY
# is True, kept for when parallel mode is re-enabled.
STAGGER_SECONDS = 4

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
    start_delay: float = 0,
) -> List[Dict[str, Any]]:
    """
    Runs one agent against one pharmacy site only. Returns a list of raw
    flat dicts (one per medicine, as the agent reported them) so the caller
    can group them by medicine. Returns an empty list on any failure
    (timeout, no result, malformed output) instead of raising.

    `start_delay`: optional sleep before this agent starts (only meaningful
    on the parallel path — see STAGGER_SECONDS). Unused (0) when
    RUN_SEQUENTIALLY is True since there's nothing to stagger against.
    """
    if start_delay:
        await asyncio.sleep(start_delay)

    llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct")

    browser = Browser(
        executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        user_data_dir=profile_dir,
        profile_directory="Default",
        permissions=["geolocation"],
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
        use_vision="auto",
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
    Searches each medicine in `medicine` across 1mg and Apollo Pharmacy and
    returns structured price + delivery data for every site. Does NOT add
    anything to any cart — extraction only.

    Runs SEQUENTIALLY by default (see RUN_SEQUENTIALLY above) — Apollo
    finishes completely before 1mg starts, so only one agent is ever
    calling Groq at a time. Slower than the old parallel version but avoids
    the Groq-contention-driven 75s-internal-timeout retries that were
    causing near-total failures under parallel load. Flip RUN_SEQUENTIALLY
    to False to go back to parallel (with a small stagger) if that
    contention stops being the bottleneck later.

    If one site fails/times out, the other site's results are still
    returned. The caller (main.py) computes 'best price' / 'fastest
    delivery' tags from the returned data; the agents themselves make no
    purchase decision.
    """
    if RUN_SEQUENTIALLY:
        apollo_raw = await _run_single_site(
            "Apollo Pharmacy",
            "https://www.apollopharmacy.in/search-medicines?source=/",
            APOLLO_PROFILE_DIR,
            medicine,
        )
        onemg_raw = await _run_single_site(
            "1mg",
            "https://www.1mg.com",
            ONEMG_PROFILE_DIR,
            medicine,
        )
    else:
        apollo_coro = _run_single_site(
            "Apollo Pharmacy",
            "https://www.apollopharmacy.in/search-medicines?source=/",
            APOLLO_PROFILE_DIR,
            medicine,
            start_delay=0,
        )
        onemg_coro = _run_single_site(
            "1mg",
            "https://www.1mg.com",
            ONEMG_PROFILE_DIR,
            medicine,
            start_delay=STAGGER_SECONDS,
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

        sites_with_delivery_info = [r for r in available_results if r.delivery_info.strip()]
        fastest_delivery_site = None
        if len(sites_with_delivery_info) == 1:
            fastest_delivery_site = sites_with_delivery_info[0].site

        med_dict = {
            "medicine_name": med.medicine_name,
            "results": [r.dict() for r in med.results],
            "best_price_site": best_price_site,
            "fastest_delivery_site": fastest_delivery_site,
        }
        output["medicines"].append(med_dict)

    return output