# Pseudocode Walkthrough -- CV Extraction LLM vs SLM

This file covers the logic of the test in pseudocode & the logic of what the python script does.

The test aims to answer one question:
**On the same CV extraction task, how does a small model compare to a large model on ACCURACY, LATENCY & COST?**

## High Level Picture

```
DEFINE a test CV                (the input)
DEFINE the correct answers      (the "ground truth")
DEFINE one extraction prompt    (the task, identical for both)

FOR each model [SLM, LLM]:
    send prompt to model
    time how long it takes to parse model's reply into structured data
    score the reply against the ground truth
    print accuracy, latency, and any mistakes
```

Key concept: everything is identical except the model. Same CV, same prompt, same scoring.
Aiming to focus mainly on model size.

## Step 1: Test Input (`data/sample_cv.txt`)

```
LOAD sample_cv = read data/sample_cv.txt
```

Real CV (my own), containing 3 jobs, each written in a **different** date format:

| Job | Date format | Why it matters |
|---|---|---|
| 1 | `"Oct 2025 - Present"` | clean dates |
| 2 | `"Nov 2022 to Mar 2025"` | "to" instead of "-" |
| 3 | `"Summer 2021/22 (Sep-Feb)"` | ambiguous, spans two years |

**Why:** real CVs are messy and inconsistent. If both models only saw clean input, we would learn nothing about which one handles the hard cases. Job 3 is a deliberate "trap" likely to separate the models.

**Note:** this went with a real (my own) CV rather than a fictional one -- there is no third-party privacy concern since it's my own data, and it keeps the test grounded in an actual messy document rather than an invented one.

```
ALSO LOAD ground_truth = data/ground_truth.json
    -> the correct {title, company, start, end, description}
       for each of the 3 jobs above, used later for scoring
```

## Step 2: The Ground Truth (`data/ground_truth.json`, the answer key)

```
LOAD ground_truth = read data/ground_truth.json
    -> JSON array of 3 records, one per job, matching the
       prompt's schema exactly:
       { title, company, start, end, description }
```

```json
{
  "title": "Full Stack Developer",
  "company": "Riverhorse Consulting Limited",
  "start": "2025-10",
  "end": "present",
  "description": "..."
}
```

**Why:** to measure accuracy you must know, in advance, what a perfect answer looks like. Because it's my own CV, I know exactly what should be extracted -- dates normalized to `YYYY-MM` so they can be compared to the model's output with exact string matching. The ground truth is the marking rubric the models are scored against.

**Note on `description`:** scored as presence/non-empty only, NOT exact-match -- free text will legitimately differ in wording between the two models, so exact-matching it would penalise correct answers for phrasing rather than accuracy.

## Step 3: Prompt (`data/prompt.md`, the task instruction)

```
LOAD prompt_template = read data/prompt.md
SET prompt = prompt_template with {SAMPLE_CV} replaced by sample_cv
```

Instruction given to **both** models, identical every time:

> Extract the work experience from this CV into JSON.
> Respond with ONLY a JSON array, no markdown fences, no commentary. Each entry must have exactly these keys:
> title, company, start (YYYY-MM), end (YYYY-MM or "present"), description (one sentence).

JSON-only, no markdown fences: model replies need to be parsed straight into structured data (Step 4). Any extra commentary or ` ```json ` fences would need to be stripped before parsing, and asking for exactly one schema up front means both models are held to the same bar.

## Step 4: Calling a Model (the `run_model` function) -- implemented

```
FUNCTION run_model(label):
    model_id = MODELS[label]
    start = now()
    response = call Gemini API(model_id, prompt)
    latency = now() - start
    raw = response.text
    cleaned = raw with ```json fences stripped
    TRY parsed = json.loads(cleaned)
    EXCEPT parse failure: parsed = None
    RETURN parsed, latency, raw
```

- **API call:** sends the prompt to a model running on Google's servers and gets text back.
- **Latency:** measured around the API call only (`time.perf_counter`, monotonic clock), because that's the delay a user would actually feel while waiting for their extraction to complete.
- **Cleaning:** models sometimes wrap JSON in ` ```json ` fences despite being told not to -- stripped before parsing.
- **Defensive error handling:** never assume the model obeyed the schema. A failed parse returns `parsed=None` rather than crashing, so it becomes a scoreable result (an SLM failure mode) instead of an unhandled exception.
- `raw` is always returned too, so a failed parse can still be inspected/debugged instead of being silently discarded.

## Step 5: Scoring (the `score` function) -- implemented

```
FUNCTION score(extracted):
    IF extracted is not a list (failed parse):
        RETURN 0 correct, every field wrong, note "no JSON array"

    FOR each truth record in ground_truth:
        match = find entry in extracted whose company name
                contains truth's company (order-independent --
                a model could plausibly return roles reshuffled)
        IF no match: every field for this role counts wrong
        ELSE:
            FOR title/company/start/end:
                fuzzy substring compare (not exact equality --
                minor spacing/wording shouldn't count as wrong)
            FOR description:
                presence/non-empty only, NOT exact-match (see
                Step 2 note -- wording legitimately differs)
    RETURN correct, total, list of mismatch notes
```

**Why fuzzy substring match rather than exact string equality:** real model output has small formatting variance (e.g. casing, trailing whitespace) that isn't a genuine extraction error -- exact-match would conflate "wrong" with "differently formatted".

## Step 6: The Main Loop (running the comparison) -- implemented

```
FUNCTION main():
    FOR each (label, model_id) in MODELS:
        parsed, latency, raw = run_model(label)
        correct, total, notes = score(parsed)
        PRINT label, latency, accuracy %, notes, raw preview
    PRINT closing cost-comparison note
```

Same prompt, same CV, same scoring function for both models -- only the model changes, matching the "Key concept" above.

## Caveats: Model Size Access (encountered while building this)

Originally planned: SLM = `gemini-2.5-flash-lite`, LLM = `gemini-2.5-pro`. Neither is usable -- both 404 "no longer available to new users".

Tried swapping to dated/preview model IDs and hit a second problem: this project's free-tier API key has quota **LIMIT 0** (not just rate limited) for every model tested above the flash-lite tier, confirmed individually for:

- `gemini-2.5-flash`
- `gemini-2.5-pro`
- `gemini-2.0-flash`
- `gemini-3-pro-preview`
- `gemini-3.1-pro-preview`
- `gemini-pro-latest` (resolves to `gemini-3.1-pro`)

Only two models actually respond on this key's free tier:

- `gemini-flash-lite-latest` -- used for SLM-class
- `gemini-flash-latest` -- used for LLM-class (stand-in)

**Impact on the experiment:** the comparison is currently Flash-Lite vs Flash, NOT Flash-Lite vs Pro. Both models are in the same family and the size gap is smaller than originally designed, so any accuracy gap observed likely **understates** what a true SLM-vs-LLM gap would look like. This is a real limitation to state explicitly in the write-up, not a result to present as-is.

**Fix (not yet done):** enable billing on the Google AI Studio project to unlock `gemini-pro-latest` quota, then swap `MODELS["LLM-class"]` back to it for the real comparison.

## What the Results Mean for the Assignment

```
IF small model accuracy ~= large model accuracy:
    -> evidence FOR the SLM recommendation:
       good enough at a fraction of cost and latency

IF small model fails on the messy dates or breaks JSON:
    -> evidence for a HYBRID design:
       SLM by default, escalate to LLM when the SLM's
       output fails validation or looks low confidence

EITHER WAY:
    latency difference -> user experience argument
    price-per-token difference -> cost-at-scale argument
    (1 CV here; a production decision would test a large amount
     -- limitation)
```
