<!-- Extraction prompt for the demo app. Forked from data/prompt.md so the
     eval experiment's frozen prompt/results aren't affected by demo tuning. -->

Extract the work experience from this CV into JSON.

Respond with ONLY a JSON array, no markdown fences, no commentary.
Each entry must have exactly these keys:
"title" (string, the job title)
"company" (string, employer name only, no location)
"start" (string, "YYYY-MM" format, or "" if the CV does not state one -- never guess or invent a date)
"end" (string, "YYYY-MM" format, "present" for an ongoing role, or "" if the CV does not state one -- never guess or invent a date)
"description" (string, a concise summary covering ALL responsibilities and
achievements listed for this role, not just the first one -- combine them
into a few sentences)

CV:
{SAMPLE_CV}
