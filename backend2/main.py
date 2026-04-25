"""
med-EZ Backend
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
import asyncio
import os

from ocr import extract_prescription
from explaination import explain_medicines
from interactions import check_interactions

# ── Groq client for chat ───────────────────────────────────────
from groq import Groq
groq_client = Groq(api_key="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")

app = FastAPI(title="med-EZ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root → landing page ────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui1.html")


# ── /api/extract  (called by ui2.html image upload button) ────
@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large. Max 10 MB.")

    # OCR extraction (uses Anthropic — ocr.py)
    extracted = await extract_prescription(image_bytes, file.content_type)
    if "error" in extracted:
        raise HTTPException(422, extracted["error"])

    medicines = extracted.get("medicines", [])
    if not medicines:
        raise HTTPException(422, "No medicines found. Please upload a clearer photo.")

    # Run explanation + interactions in parallel
    explanations, interactions = await asyncio.gather(
        explain_medicines(medicines),
        check_interactions(medicines),
    )

    # Merge explanation into each medicine
    explain_map = {e["brand_name"]: e for e in explanations}
    enriched = [{**med, **explain_map.get(med["brand_name"], {})} for med in medicines]

    return {
        "medicines":    enriched,
        "interactions": interactions,
        "doctor_name":  extracted.get("doctor_name"),
        "date":         extracted.get("date"),
        "confidence":   extracted.get("confidence", "medium"),
        "raw_text":     extracted.get("raw_text"),
    }


# ── /api/chat  (called by u3.html chatbot) ────────────────────
class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@app.post("/api/chat")
async def chat(req: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Dr. AI, a friendly medical assistant for Indian patients. "
                "Give clear, simple health guidance. "
                "Always remind users to consult a real doctor for diagnosis or treatment."
            ),
        }
    ]
    for msg in req.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1000,
    )
    return {"reply": response.choices[0].message.content}


# ── /health ────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy"}


# ── Serve frontend HTML files — MUST BE LAST ──────────────────
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")