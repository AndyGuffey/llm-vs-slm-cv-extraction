import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT_DIR = Path(__file__).parent.parent
BACKEND_DIR = Path(__file__).parent

# Forked from data/prompt.md -- the demo prompt is tuned independently so it
# doesn't affect the eval experiment's already-recorded results.
PROMPT_TEMPLATE = (BACKEND_DIR / "prompt.md").read_text(encoding="utf-8")

# Schema instructions without the "CV:\n{SAMPLE_CV}" tail, for the escalation
# path where the CV is attached as a file instead of interpolated as text.
INSTRUCTIONS = PROMPT_TEMPLATE.split("\n\nCV:\n")[0]

load_dotenv(ROOT_DIR / ".env")

# Which backend run_model() calls -- defaults to the local Ollama model,
# escalating to Gemini on low confidence (see should_escalate). Override
# with MODEL_BACKEND=gemini to skip local inference entirely.
MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "ollama")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_ID = "llama3.2:3b"
GEMINI_MODEL_ID = "gemini-flash-lite-latest"

EXPECTED_FIELDS = ("title", "company", "start", "end", "description")
DATE_FIELDS = ("start", "end")
NON_DATE_FIELDS = tuple(f for f in EXPECTED_FIELDS if f not in DATE_FIELDS)

# Below this average confidence (or on a parse failure / empty result), escalate
# from the primary MODEL_BACKEND to Gemini for a second attempt.
ESCALATION_CONFIDENCE_THRESHOLD = float(os.environ.get("ESCALATION_CONFIDENCE_THRESHOLD", "0.6"))

_gemini_client = None


def _clean_and_parse(raw: str):
    # Models sometimes wrap JSON in ```json fences despite being told not to.
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def run_ollama(cv_text: str, model_id: str = OLLAMA_MODEL_ID):
    #? Call the local Ollama model, return (parsed json or None, latency in seconds, raw response text)
    prompt = PROMPT_TEMPLATE.format(SAMPLE_CV=cv_text)

    start = time.perf_counter()
    response = httpx.post(
        OLLAMA_URL,
        json={"model": model_id, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    latency = time.perf_counter() - start

    raw = response.json()["response"].strip()
    return _clean_and_parse(raw), latency, raw


def run_gemini(cv_text: str, model_id: str = GEMINI_MODEL_ID):
    #? Call the Gemini API, return (parsed json or None, latency in seconds, raw response text)
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = PROMPT_TEMPLATE.format(SAMPLE_CV=cv_text)

    start = time.perf_counter()
    response = _gemini_client.models.generate_content(model=model_id, contents=prompt)
    latency = time.perf_counter() - start

    raw = response.text.strip()
    return _clean_and_parse(raw), latency, raw


def run_gemini_multimodal(raw_bytes: bytes, model_id: str = GEMINI_MODEL_ID):
    #? Escalation path for PDFs: send the file itself instead of pre-extracted
    #? text, so Gemini reads the layout visually rather than inheriting
    #? pypdf's (possibly column-scrambled) reading order.
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = INSTRUCTIONS + "\n\nThe CV is attached below as a PDF file."

    start = time.perf_counter()
    response = _gemini_client.models.generate_content(
        model=model_id,
        contents=[prompt, types.Part.from_bytes(data=raw_bytes, mime_type="application/pdf")],
    )
    latency = time.perf_counter() - start

    raw = response.text.strip()
    return _clean_and_parse(raw), latency, raw


def run_model(cv_text: str):
    #? Dispatch to whichever backend MODEL_BACKEND selects.
    if MODEL_BACKEND == "ollama":
        return run_ollama(cv_text)
    return run_gemini(cv_text)


def average_confidence(experience):
    if not experience:
        return 0.0
    return sum(role["confidence"] for role in experience) / len(experience)


def should_escalate(parsed, experience):
    #? Return why the primary attempt looks unreliable, or None if it's fine.
    if parsed is None:
        return "parse_failed"
    if not experience:
        return "empty"
    if average_confidence(experience) < ESCALATION_CONFIDENCE_THRESHOLD:
        return "low_confidence"
    return None


def run_escalation(raw_bytes: bytes, cv_text: str, filename: str):
    #? Retry with a stronger path. Returns (parsed, latency, raw), or None if
    #? there's no viable upgrade left for this file type/backend combination.
    if filename.lower().endswith(".pdf"):
        return run_gemini_multimodal(raw_bytes)
    if MODEL_BACKEND != "gemini":
        return run_gemini(cv_text)
    return None


def _looks_like_date(value: str) -> bool:
    #? A real YYYY-MM date, "present", or genuinely blank (the CV may not
    #? state a date -- see prompt.md) all count as valid. Placeholder text
    #? a model might emit instead of admitting it doesn't know -- "unknown",
    #? the literal string "YYYY-MM", etc. -- does not.
    value = value.strip().lower()
    if value in ("", "present"):
        return True
    return len(value) == 7 and value[:4].isdigit() and value[5:7].isdigit()


def score_confidence(parsed):
    #? Heuristic per-role confidence, since a local SLM's self-reported
    #? confidence isn't reliable enough to surface in a demo. Each role
    #? gets a 0-1 score: fraction of non-date fields present, plus a shape
    #? check on start/end (not plain presence -- a hallucinated placeholder
    #? like "YYYY-MM" is non-empty but should still cost the role marks).
    if not isinstance(parsed, list):
        return []

    results = []
    for role in parsed:
        if not isinstance(role, dict):
            continue

        checks = [bool(str(role.get(field, "")).strip()) for field in NON_DATE_FIELDS]
        checks += [_looks_like_date(str(role.get(field, ""))) for field in DATE_FIELDS]

        confidence = round(sum(checks) / len(checks), 2)
        results.append({**role, "confidence": confidence})

    return results
