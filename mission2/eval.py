"""
Mission 2 applied method: does the hybrid approach (local Ollama primary,
confidence-gated escalation to Gemini) hold up against reality, and against
the always-cloud alternative rejected in Mission 1?

Reuses the actual production functions from backend/extraction.py and
backend/file_parsing.py -- this runs the real should_escalate/run_escalation
logic, not a reimplementation of it, so results reflect what the app
actually does.

For each CV, three paths are compared against hand-written ground truth:
  A. Ollama-only   -- primary path, escalation disabled
  B. Gemini-only   -- the always-cloud alternative rejected in Mission 1
  C. Hybrid        -- the real production path (primary + escalation if triggered)
"""

import json
import sys
from pathlib import Path

MISSION2_DIR = Path(__file__).parent
DATA_DIR = MISSION2_DIR / "data"
BACKEND_DIR = MISSION2_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from extraction import (  # noqa: E402
    run_ollama,
    run_gemini,
    run_escalation,
    should_escalate,
    score_confidence,
    average_confidence,
    OLLAMA_MODEL_ID,
    GEMINI_MODEL_ID,
)
from file_parsing import extract_text  # noqa: E402

CVS = [
    {"file": "1.AG_CV_simple.pdf", "ground_truth": "gt_1.json"},
    {"file": "2.JD_CV2.docx", "ground_truth": "gt_2.json"},
    {"file": "3.A_G.pdf", "ground_truth": "gt_3.json"},
]

EXACT_FIELDS = ("title", "company", "start", "end")


def find_match(truth, extracted):
    #? Match by company when the ground truth has one; some CVs (casual/
    #? informal roles) don't name an employer, so fall back to title.
    if truth.get("company"):
        match = next(
            (e for e in extracted if truth["company"].lower() in str(e.get("company", "")).lower()),
            None,
        )
        if match is not None:
            return match
    return next(
        (e for e in extracted if truth["title"].lower() in str(e.get("title", "")).lower()),
        None,
    )


def field_correct(want: str, got: str) -> bool:
    #? Fuzzy substring match, except when the ground truth field is
    #? deliberately blank (CV gave no date) -- an empty "want" is a
    #? substring of everything, so without this branch a hallucinated
    #? date would score as correct against a blank ground truth.
    if want == "":
        return got == ""
    return want in got or got in want


def score(extracted, ground_truth):
    #? Compare extracted roles to ground truth. Returns (correct, total, notes).
    correct = 0
    total = 0
    notes = []

    if not isinstance(extracted, list):
        notes.append("model did not return a JSON array")
        total = len(ground_truth) * (len(EXACT_FIELDS) + 1)
        return correct, total, notes

    for truth in ground_truth:
        match = find_match(truth, extracted)
        label = truth.get("company") or truth["title"]

        if match is None:
            notes.append(f"missing role: {label}")
            total += len(EXACT_FIELDS) + 1
            continue

        for field in EXACT_FIELDS:
            total += 1
            got = str(match.get(field, "")).strip().lower()
            want = str(truth[field]).strip().lower()
            if field_correct(want, got):
                correct += 1
            else:
                notes.append(f"{label} / {field}: got '{match.get(field)}', expected '{truth[field]}'")

        total += 1
        if match.get("description"):
            correct += 1
        else:
            notes.append(f"{label} / description: missing")

    return correct, total, notes


def report(label, parsed, latency, ground_truth, escalated=None, escalation_reason=None):
    experience = score_confidence(parsed)
    correct, total, notes = score(parsed, ground_truth)
    pct = 100 * correct / total if total else 0

    print(f"\n--- {label} ---")
    print(f"Latency:            {latency:.2f}s")
    print(f"Accuracy:           {correct}/{total} fields ({pct:.0f}%)")
    print(f"Avg confidence:     {average_confidence(experience):.2f}")
    if escalated is not None:
        print(f"Escalated:          {escalated}" + (f" ({escalation_reason})" if escalated else ""))
    if notes:
        print("Issues:")
        for n in notes:
            print(f"  - {n}")
    else:
        print("Issues:             none -- all fields matched")

    return {
        "label": label,
        "latency": round(latency, 2),
        "correct": correct,
        "total": total,
        "accuracy_pct": round(pct, 1),
        "avg_confidence": round(average_confidence(experience), 2),
        "escalated": escalated,
        "escalation_reason": escalation_reason,
        "notes": notes,
    }


def main():
    all_results = []

    for cv in CVS:
        raw_bytes = (DATA_DIR / cv["file"]).read_bytes()
        cv_text = extract_text(raw_bytes, cv["file"])
        ground_truth = json.loads((DATA_DIR / cv["ground_truth"]).read_text(encoding="utf-8"))

        print("=" * 70)
        print(f"CV: {cv['file']}")
        print("=" * 70)

        # Path A: Ollama-only (primary path, no escalation allowed)
        parsed_a, latency_a, _ = run_ollama(cv_text)
        result_a = report(f"A. Ollama-only ({OLLAMA_MODEL_ID})", parsed_a, latency_a, ground_truth)

        # Path B: Gemini-only (the always-cloud alternative rejected in Mission 1)
        parsed_b, latency_b, _ = run_gemini(cv_text)
        result_b = report(f"B. Gemini-only ({GEMINI_MODEL_ID})", parsed_b, latency_b, ground_truth)

        # Path C: Hybrid -- the real production logic. Reuses Path A's
        # result rather than re-calling Ollama, since should_escalate is
        # a pure function of that result.
        experience_a = score_confidence(parsed_a)
        reason = should_escalate(parsed_a, experience_a)

        if reason:
            result = run_escalation(raw_bytes, cv_text, cv["file"])
            if result is not None:
                parsed_c, latency_esc, _ = result
                total_latency = latency_a + latency_esc
                result_c = report(
                    "C. Hybrid (escalated)", parsed_c, total_latency, ground_truth,
                    escalated=True, escalation_reason=reason,
                )
            else:
                result_c = report(
                    "C. Hybrid (escalation unavailable)", parsed_a, latency_a, ground_truth,
                    escalated=False, escalation_reason=reason,
                )
        else:
            result_c = report(
                "C. Hybrid (no escalation needed)", parsed_a, latency_a, ground_truth,
                escalated=False, escalation_reason=None,
            )

        all_results.append({"cv": cv["file"], "paths": [result_a, result_b, result_c]})

    out_path = MISSION2_DIR / "results.json"
    out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\n{'=' * 70}\nResults written to {out_path}")
    print("Cost note: Ollama is $0 marginal cost (local compute). Gemini is")
    print("billed per token -- cite published gemini-flash-lite-latest /")
    print("gemini-flash-latest pricing against these CVs' token lengths for")
    print("an at-scale cost comparison; both were free-tier for this run.")


if __name__ == "__main__":
    main()
