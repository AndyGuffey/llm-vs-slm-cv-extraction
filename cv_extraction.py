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
    "LLM-class (Pro)": "gemini-pro-latest",
}

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def test_connection():
    response = client.models.generate_content(
        model=MODELS["SLM-class (Flash-Lite)"],
        contents="Reply with exactly one word: connected",
    )
    print(response.text)

def run_model():
    # Call one model, return (parsed json, latency in seconds, raw response text)
    pass

def score():
    # Compare the model's output to the ground truth and return a score
    pass

if __name__ == "__main__":
    test_connection()
















