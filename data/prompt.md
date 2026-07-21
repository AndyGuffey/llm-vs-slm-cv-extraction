<!-- Extraction prompt (will be used for both models) -->

Extract the work experience from this CV into JSON.

Respond with ONLY a JSON array, no markdown fences, no commentary.
Each entry must have exactly these keys:
"title" (string, the job title)
"company" (string, employer name only, no location)
"start" (string, "YYYY-MM" format)
"end" (string, "YYYY-MM" format, or "present")
"description" (string, one sentence)

CV:
{SAMPLE_CV}
