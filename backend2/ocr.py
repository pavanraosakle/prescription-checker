import base64
import json
import os
from groq import Groq

GROQ_API_KEY = "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"

SYSTEM_PROMPT = """You are a medical prescription parser with expertise in Indian prescriptions.
Extract structured data from prescription images accurately.
Always return valid JSON only — no markdown, no explanation, no preamble.
If a brand name looks like an Indian drug (e.g. Crocin, Augmentin, Glycomet, Pantop, Dolo),
make your best guess at the generic/active ingredient and set confidence to medium.
"""

USER_PROMPT = """Extract all medicines from this prescription image and return a JSON object.
For each medicine extract:
- brand_name, generic_name, dose, frequency, duration, route, instructions

Also extract:
- raw_text, doctor_name, date
- confidence: "high", "medium", or "low"

Return ONLY this JSON structure:
{
  "medicines": [{"brand_name": "...","generic_name": "...","dose": "...","frequency": "...","duration": "...","route": "...","instructions": "..."}],
  "raw_text": "...","doctor_name": "...","date": "...","confidence": "high|medium|low"
}
If not a prescription return: { "error": "reason" }
"""

async def extract_prescription(image_bytes: bytes, content_type: str) -> dict:
    if content_type == "application/pdf":
        return {"error": "PDF not supported. Please upload JPG or PNG."}

    client = Groq(api_key=GROQ_API_KEY)
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}},
                {"type": "text", "text": USER_PROMPT}
            ]}
        ],
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "Could not parse prescription. Please try a clearer image."}