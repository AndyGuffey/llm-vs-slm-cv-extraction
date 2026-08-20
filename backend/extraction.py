import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
PROMPT_TEMPLATE = (DATA_DIR / "prompt.md").read_text(encoding="utf-8")

load_dotenv(ROOT_DIR / ".env")

# Which backend run_model() calls -- "gemini" while Ollama isn't set up
# locally, switch to "ollama" once it is. Same prompt/parsing either way.
MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "gemini")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL_ID = "llama3.2:3b"
GEMINI_MODEL_ID = "gemini-flash-lite-latest"

EXPECTED_FIELDS = ("title", "company", "start", "end", "description")

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


def run_model(cv_text: str):
    #? Dispatch to whichever backend MODEL_BACKEND selects.
    if MODEL_BACKEND == "ollama":
        return run_ollama(cv_text)
    return run_gemini(cv_text)


def score_confidence(parsed):
    #? Heuristic per-role confidence, since a local SLM's self-reported
    #? confidence isn't reliable enough to surface in a demo. Each role
    #? gets a 0-1 score: fraction of expected fields present, plus a
    #? shape check on start/end looking like real dates.
    if not isinstance(parsed, list):
        return []

    results = []
    for role in parsed:
        if not isinstance(role, dict):
            continue

        checks = [bool(str(role.get(field, "")).strip()) for field in EXPECTED_FIELDS]

        for field in ("start", "end"):
            value = str(role.get(field, "")).strip().lower()
            looks_like_date = value == "present" or (
                len(value) == 7 and value[:4].isdigit() and value[5:7].isdigit()
            )
            checks.append(looks_like_date)

        confidence = round(sum(checks) / len(checks), 2)
        results.append({**role, "confidence": confidence})

    return results
