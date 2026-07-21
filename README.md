# LLM vs SLM: CV Extraction

A small experiment comparing a large language model against a small language model on the same CV-extraction task, measuring **accuracy**, **latency**, and **cost**.

Both models are given the identical prompt and CV, and are scored against the same hand-written ground truth. See [`pseudo_code.md`](pseudo_code.md) for the full step-by-step logic walkthrough.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add a Gemini API key:

```
GEMINI_API_KEY=your_key_here
```

## Running

```bash
python cv_extraction.py
```

This runs both models against `data/sample_cv.txt`, scores each reply against `data/ground_truth.json`, and prints latency, accuracy, and any mismatches for each.

## Project structure

```
cv_extraction.py       -- run_model(), score(), main()
data/
  sample_cv.txt         -- test input: a real CV with 3 jobs, each in a different date format
  ground_truth.json     -- the correct extraction, used for scoring
  prompt.md              -- the extraction prompt sent to both models
pseudo_code.md          -- pseudocode walkthrough of the test logic
```

## Caveats: model size access

The original plan was to compare `gemini-2.5-flash-lite` (SLM) against `gemini-2.5-pro` (LLM). Neither could be used:

- Both `gemini-2.5-flash-lite` and `gemini-2.5-pro` return 404 "no longer available to new users".
- Every model tried above the flash-lite tier returned a **quota limit of 0** on this project's free-tier API key (not just a rate limit) -- confirmed individually for `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-3-pro-preview`, `gemini-3.1-pro-preview`, and `gemini-pro-latest`.

The only models that actually respond on this key's free tier are `gemini-flash-lite-latest` and `gemini-flash-latest`, so those are what's currently wired up:

| Role | Model |
|---|---|
| SLM-class | `gemini-flash-lite-latest` |
| LLM-class | `gemini-flash-latest` |

**This means the current comparison is Flash-Lite vs Flash, not Flash-Lite vs Pro.** Both models are in the same family, so the size gap under test is smaller than originally designed -- any accuracy difference observed likely *understates* what a true SLM-vs-LLM gap would look like. This is a limitation to call out explicitly in the write-up, not a result to present as a fair small-vs-large comparison.

To run the intended Pro-scale comparison, billing needs to be enabled on the Google AI Studio project to unlock `gemini-pro-latest` quota, then `MODELS["LLM-class"]` in `cv_extraction.py` swapped back to it.
