# prescription-checker
# RxDigitizer Backend

Prescription OCR + drug interaction checker API built for the hackathon.

## Stack
- **FastAPI** — API framework
- **Claude Vision API** — OCR + plain-language explanations
- **RxNorm (NLM)** — Free drug interaction checker, no key needed

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run the server
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | **Main endpoint** — full pipeline (OCR + explain + interactions) |
| POST | `/ocr` | OCR only — returns raw structured data |
| POST | `/explain` | Explain medicines in plain language |
| POST | `/interactions` | Check drug interactions via RxNorm |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs (Swagger UI) |

## Quick Test

```bash
# Test with a prescription image
curl -X POST http://localhost:8000/analyze \
  -F "file=@prescription.jpg"
```

## Sample Response

```json
{
  "medicines": [
    {
      "brand_name": "Crocin 500",
      "generic_name": "paracetamol",
      "dose": "500mg",
      "frequency": "TDS",
      "duration": "5 days",
      "what_it_is": "A painkiller that reduces fever and relieves mild pain",
      "how_to_take": "Take 1 tablet by mouth 3 times a day, after meals, for 5 days",
      "common_side_effects": ["Mild nausea", "Stomach upset", "Dizziness"],
      "important_warning": "Do not take more than 4 tablets in 24 hours",
      "safe_with_food": true
    }
  ],
  "interactions": {
    "has_interactions": false,
    "interaction_pairs": [],
    "drugs_checked": ["Crocin 500"],
    "drugs_skipped": []
  },
  "doctor_name": "Dr. Sharma",
  "date": "22/04/2025",
  "confidence": "high",
  "raw_text": "..."
}
```

## Architecture

```
POST /analyze
    │
    ├── ocr.py          → Claude Vision API (image → structured JSON)
    │
    ├── explainer.py    → Claude API (medicines → plain-language cards)  ─┐ parallel
    │                                                                      │
    └── interactions.py → RxNorm free API (generics → interaction check) ─┘
```

## File Structure

```
rx_backend/
├── main.py           # FastAPI app, routes
├── models.py         # Pydantic request/response models
├── ocr.py            # Claude Vision OCR + extraction
├── explainer.py      # Claude plain-language explanation
├── interactions.py   # RxNorm drug interaction checker
├── requirements.txt
├── .env.example
└── README.md
```

## Deploying to Render / Railway (free tier)

1. Push to GitHub
2. Connect to Render → New Web Service → Python
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add `ANTHROPIC_API_KEY` as environment variable