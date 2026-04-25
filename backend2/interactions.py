"""
interactions.py — Drug interaction checker via RxNorm (NLM) free API
No API key required.
"""

import httpx
from typing import Any

RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)

INDIA_BRAND_OVERRIDES: dict[str, str] = {
    "crocin": "paracetamol", "dolo": "paracetamol", "calpol": "paracetamol",
    "combiflam": "ibuprofen paracetamol", "brufen": "ibuprofen",
    "zerodol": "aceclofenac", "voveran": "diclofenac",
    "pan": "pantoprazole", "pantop": "pantoprazole",
    "omez": "omeprazole", "rantac": "ranitidine",
    "augmentin": "amoxicillin clavulanate", "mox": "amoxicillin",
    "cifran": "ciprofloxacin", "glycomet": "metformin",
    "ecosprin": "aspirin", "stamlo": "amlodipine",
    "telma": "telmisartan", "atorva": "atorvastatin",
    "clavix": "clopidogrel", "deplatt": "clopidogrel",
    "allegra": "fexofenadine", "cetirizine": "cetirizine",
    "montair": "montelukast", "asthalin": "salbutamol",
    "azithral": "azithromycin", "zithromax": "azithromycin",
}

def _resolve_generic(medicine: dict[str, Any]) -> str | None:
    generic = medicine.get("generic_name")
    if generic and generic.strip():
        return generic.strip().lower()
    brand = medicine.get("brand_name", "").lower().strip()
    brand_base = brand.split()[0] if brand else ""
    if brand_base in INDIA_BRAND_OVERRIDES:
        return INDIA_BRAND_OVERRIDES[brand_base]
    return brand if brand else None

async def _get_rxcui(client: httpx.AsyncClient, drug_name: str) -> str | None:
    try:
        resp = await client.get(f"{RXNORM_BASE}/rxcui.json",
            params={"name": drug_name, "search": "1"}, timeout=TIMEOUT)
        return resp.json().get("idGroup", {}).get("rxnormId", [None])[0]
    except Exception:
        return None

async def _check_pair(client: httpx.AsyncClient, rxcui1: str, rxcui2: str) -> list[dict]:
    try:
        resp = await client.get(f"{RXNORM_BASE}/interaction/list.json",
            params={"rxcuis": f"{rxcui1} {rxcui2}"}, timeout=TIMEOUT)
        return (resp.json().get("fullInteractionTypeGroup", [{}])[0]
            .get("fullInteractionType", [{}])[0]
            .get("interactionPair", []))
    except Exception:
        return []

async def check_interactions(medicines: list[dict[str, Any]]) -> dict[str, Any]:
    if len(medicines) < 2:
        return {"has_interactions": False, "interaction_pairs": [],
                "drugs_checked": [], "drugs_skipped": []}

    async with httpx.AsyncClient() as client:
        resolved, skipped = [], []
        for med in medicines:
            generic = _resolve_generic(med)
            if generic:
                rxcui = await _get_rxcui(client, generic)
                if rxcui:
                    resolved.append((med["brand_name"], generic, rxcui))
                else:
                    skipped.append(med.get("brand_name", "unknown"))
            else:
                skipped.append(med.get("brand_name", "unknown"))

        interaction_pairs = []
        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                brand1, _, rxcui1 = resolved[i]
                brand2, _, rxcui2 = resolved[j]
                for pair in await _check_pair(client, rxcui1, rxcui2):
                    desc = pair.get("description", "")
                    if desc:
                        interaction_pairs.append({
                            "drug_1": brand1, "drug_2": brand2,
                            "severity": pair.get("severity"),
                            "description": desc, "source": "rxnorm"
                        })

    return {
        "has_interactions": len(interaction_pairs) > 0,
        "interaction_pairs": interaction_pairs,
        "drugs_checked": [r[0] for r in resolved],
        "drugs_skipped": skipped,
    }