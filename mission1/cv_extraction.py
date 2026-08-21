import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

SAMPLE_CV = (DATA_DIR / "sample_cv.txt").read_text(encoding="utf-8")
GROUND_TRUTH = json.loads((DATA_DIR / "ground_truth.json").read_text(encoding="utf-8"))
PROMPT_TEMPLATE = (DATA_DIR / "prompt.md").read_text(encoding="utf-8")
PROMPT = PROMPT_TEMPLATE.format(SAMPLE_CV=SAMPLE_CV)

MODELS = {
    "SLM-class (Flash-Lite)": "gemini-flash-lite-latest",
    # gemini-pro-latest is 429/quota=0 on the free tier for this
    # project; gemini-flash-latest is the largest model this key can
    # actually call -- not true Pro-scale, worth noting as a
    # limitation in the writeup.
    "LLM-class (Flash)": "gemini-flash-latest",
}

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def test_connection():
    response = client.models.generate_content(
        model=MODELS["SLM-class (Flash-Lite)"],
        contents="Reply with exactly one word: connected",
    )
    print(response.text)

def run_model(model_id: str):
    #? Call one model, return (parsed json, latency in seconds, raw response text)

    # perf_counter is monotonic, so it isn't skewed by system clock
    # adjustments -- start/stop bracket only the API call itself.
    start = time.perf_counter()
    response = client.models.generate_content(
        model=MODELS[model_id],
        contents=PROMPT,
    )
    latency = time.perf_counter() - start

    raw = response.text.strip()

    # Despite the prompt asking for no markdown fences, models
    # sometimes wrap the JSON in ```json ... ``` anyway. Strip it
    # so json.loads doesn't fail on otherwise-valid output.
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    # Never assume the model obeyed the schema -- the SLM in
    # particular may return malformed JSON. A failed parse is
    # itself a result worth recording, not a crash.
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = None

    # raw is returned alongside parsed so a failed parse can still
    # be inspected/debugged instead of being silently discarded.
    return parsed, latency, raw
    

EXACT_FIELDS = ("title", "company", "start", "end")


def score(extracted):
    #? Compare the model's output to the ground truth and return (correct, total, notes)
    correct = 0
    total = 0
    notes = []

    # A failed parse or wrong shape (not a list) means nothing can be
    # matched -- every field across every role counts as wrong.
    if not isinstance(extracted, list):
        notes.append("model did not return a JSON array")
        total = len(GROUND_TRUTH) * (len(EXACT_FIELDS) + 1)
        return correct, total, notes

    for truth in GROUND_TRUTH:
        # Match by company rather than list position -- a model could
        # plausibly return roles in a different order.
        match = next(
            (e for e in extracted if truth["company"].lower() in str(e.get("company", "")).lower()),
            None,
        )

        if match is None:
            notes.append(f"missing role at {truth['company']}")
            total += len(EXACT_FIELDS) + 1
            continue

        for field in EXACT_FIELDS:
            total += 1
            got = str(match.get(field, "")).lower()
            want = str(truth[field]).lower()
            # Fuzzy substring match, not exact equality -- minor
            # spacing/wording differences shouldn't count as wrong.
            if want in got or got in want:
                correct += 1
            else:
                notes.append(f"{truth['company']} / {field}: got '{match.get(field)}', expected '{truth[field]}'")

        # description is scored as presence-only, not exact-match --
        # free text will legitimately differ in wording between models.
        total += 1
        if match.get("description"):
            correct += 1
        else:
            notes.append(f"{truth['company']} / description: missing")

    return correct, total, notes


def main():
    print("=" * 70)
    print("CV EXTRACTION EXPERIMENT: small vs large model (Gemini)")
    print("=" * 70)
    for label, model_id in MODELS.items():
        print(f"\n--- {label} ({model_id}) ---")
        parsed, latency, raw = run_model(label)
        correct, total, notes = score(parsed)
        print(f"Latency:  {latency:.2f}s")
        print(f"Accuracy: {correct}/{total} fields correct "
              f"({100 * correct / total:.0f}%)")
        if notes:
            print("Issues:")
            for n in notes:
                print(f"  - {n}")
        else:
            print("Issues:   none -- all fields matched")
        print("Raw output (first 400 chars):")
        print(raw[:400])
    print("\nDone. Both models are free on AI Studio's free tier; cite")
    print("published per-token pricing for the at-scale cost comparison.")

if __name__ == "__main__":
    # test connection commented out to avoid unnecessary API calls during normal runs
    # test_connection() 
    main()















