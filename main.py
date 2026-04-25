from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
from groq import Groq
import base64, json, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Root redirect ──────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui1.html")


# ── API: Extract prescription from image ───────────────────────
@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{file.content_type};base64,{image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are a medical prescription parser. "
                            "Return ONLY this JSON, no markdown: "
                            '{"medicines":[{"brand_name":"","generic_name":"","dose":"",'
                            '"frequency":"","duration":"","route":"","instructions":""}],'
                            '"doctor_name":"","date":"","confidence":"high"}'
                        ),
                    },
                ],
            }
        ],
        max_tokens=1500,
    )
    raw = (
        response.choices[0].message.content
        .strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    return json.loads(raw)


# ── API: Explain medicines in plain language ───────────────────
class ExplainRequest(BaseModel):
    medicines: List[dict]


@app.post("/api/explain")
async def explain(req: ExplainRequest):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": (
                    "Explain each medicine for an Indian patient. "
                    "Return ONLY a JSON array, no markdown: "
                    '[{"brand_name":"...","what_it_is":"...","how_to_take":"...",'
                    '"common_side_effects":[],"important_warning":"...","safe_with_food":true}] '
                    f"Medicines: {json.dumps(req.medicines)}"
                ),
            }
        ],
        max_tokens=1500,
    )
    raw = (
        response.choices[0].message.content
        .strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    return json.loads(raw)


# ── API: Chat with Dr. AI ──────────────────────────────────────
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
                "Give clear simple health guidance. Always remind users to consult a real doctor."
            ),
        }
    ]
    for msg in req.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": req.message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1000,
    )
    return {"reply": response.choices[0].message.content}


# ── Serve frontend files (must be LAST) ───────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")