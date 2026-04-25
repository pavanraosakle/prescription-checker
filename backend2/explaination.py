import json
import os
from groq import Groq

GROQ_API_KEY = "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"

SYSTEM_PROMPT = """You are a friendly medical assistant helping patients in India understand their prescriptions.
Explain medicines in simple, clear English that a non-medical person can understand.
Always return valid JSON only — no markdown, no explanation, no preamble.
"""

def _build_user_prompt(medicines: list) -> str:
    return f"""Explain each medicine below for a patient in India. Use simple, friendly language.

Medicines:
{json.dumps(medicines, indent=2)}

For each medicine return:
- brand_name, what_it_is, how_to_take
- common_side_effects: array of 2-3 side effects
- important_warning: most critical thing to know, null if nothing critical
- safe_with_food: true if with food, false if empty stomach, null if doesn't matter

Return ONLY a JSON array:
[
  {{
    "brand_name": "...",
    "what_it_is": "...",
    "how_to_take": "...",
    "common_side_effects": ["...", "...", "..."],
    "important_warning": "...",
    "safe_with_food": true
  }}
]"""


async def explain_medicines(medicines: list) -> list:
    if not medicines:
        return []

    client = Groq(api_key=GROQ_API_KEY)

    slim_meds = [
        {
            "brand_name": m.get("brand_name", ""),
            "generic_name": m.get("generic_name"),
            "dose": m.get("dose"),
            "frequency": m.get("frequency"),
            "duration": m.get("duration"),
            "route": m.get("route"),
            "instructions": m.get("instructions"),
        }
        for m in medicines
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(slim_meds)}
        ],
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    return [
        {
            "brand_name": m.get("brand_name", ""),
            "what_it_is": None,
            "how_to_take": f"{m.get('dose', '')} {m.get('frequency', '')}".strip() or None,
            "common_side_effects": [],
            "important_warning": None,
            "safe_with_food": None,
        }
        for m in medicines
    ]