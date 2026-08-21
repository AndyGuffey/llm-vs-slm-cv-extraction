import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "extractions.jsonl"


def log_extraction(**fields):
    #? Append one JSON line per /extract request. Metadata only -- never log
    #? raw CV text or model output, since CVs carry names/emails/phone numbers.
    LOG_DIR.mkdir(exist_ok=True)
    event = {"timestamp": datetime.now(timezone.utc).isoformat(), **fields}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
