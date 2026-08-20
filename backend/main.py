from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from extraction import run_model, score_confidence
from file_parsing import extract_text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/extract")
async def extract(file: UploadFile):
    raw_bytes = await file.read()
    cv_text = extract_text(raw_bytes, file.filename)

    parsed, latency, raw = run_model(cv_text)
    experience = score_confidence(parsed)

    return {
        "experience": experience,
        "latency": round(latency, 2),
        "raw": raw if parsed is None else None,
    }
