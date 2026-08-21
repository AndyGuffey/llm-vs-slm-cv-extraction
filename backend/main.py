from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from extraction import (
    GEMINI_MODEL_ID,
    MODEL_BACKEND,
    OLLAMA_MODEL_ID,
    average_confidence,
    run_escalation,
    run_model,
    score_confidence,
    should_escalate,
)
from file_parsing import extract_text
from logging_utils import log_extraction

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

    parsed, primary_latency, raw = run_model(cv_text)
    experience = score_confidence(parsed)

    reason = should_escalate(parsed, experience)
    escalated = False
    escalation_latency = None
    model_used = OLLAMA_MODEL_ID if MODEL_BACKEND == "ollama" else GEMINI_MODEL_ID
    if reason:
        try:
            result = run_escalation(raw_bytes, cv_text, file.filename)
        except Exception:
            result = None
        if result is not None:
            parsed, escalation_latency, raw = result
            experience = score_confidence(parsed)
            escalated = True
            model_used = GEMINI_MODEL_ID

    total_latency = primary_latency + (escalation_latency or 0)

    log_extraction(
        filename=file.filename,
        model_backend=MODEL_BACKEND,
        model_used=model_used,
        latency_primary=round(primary_latency, 2),
        latency_escalation=round(escalation_latency, 2) if escalation_latency is not None else None,
        latency_total=round(total_latency, 2),
        escalated=escalated,
        escalation_reason=reason if escalated else None,
        num_roles=len(experience),
        average_confidence=average_confidence(experience),
        parse_failed=parsed is None,
    )

    return {
        "experience": experience,
        "latency": round(total_latency, 2),
        "raw": raw if parsed is None else None,
        "escalated": escalated,
        "escalation_reason": reason if escalated else None,
    }
