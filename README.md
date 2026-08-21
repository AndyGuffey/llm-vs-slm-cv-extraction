# CV Extraction Demo

Upload a CV (PDF/DOCX), auto-fill its experience section, and see a per-role confidence score. FastAPI backend + React (Vite) frontend.

The extraction model is swappable via the `MODEL_BACKEND` env var, with automatic escalation to Gemini when the primary model's confidence is low:

| `MODEL_BACKEND` | Model | Notes |
|---|---|---|
| `ollama` (default) | `llama3.2:3b`, local | simulates a company running its own locally-hosted SLM, no cloud key needed; low-confidence extractions escalate to Gemini |
| `gemini` | Gemini API | cloud-hosted, skips local inference entirely |

## Setup

Copy `.env.example` to `.env` in the repo root and add a Gemini API key (used both directly when `MODEL_BACKEND=gemini`, and as the escalation model when running on Ollama):

```
GEMINI_API_KEY=your_key_here
```

The default backend is Ollama, so also install it and pull the model:
```bash
ollama pull llama3.2:3b   # once -- requires Ollama installed (https://ollama.com)
ollama serve              # if it isn't already running in the background
```

**Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

To skip local inference and use Gemini directly instead:
```bash
MODEL_BACKEND=gemini uvicorn main:app --reload
```

**Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

Then open the Vite dev server URL (typically `http://localhost:5173`).

## Project structure

```
backend/                 -- FastAPI app (extraction, file parsing, per-extraction logging)
  prompt.md               -- extraction prompt
frontend/                -- React + Vite UI
mission1/                -- assignment 1: the standalone LLM-vs-SLM CV-extraction experiment
                             this demo grew out of (unrelated codebase, own README)
```

## Origin

This app grew out of [`mission1`](mission1/README.md), a standalone experiment comparing a large vs. small language model on CV extraction. That experiment is otherwise unrelated to this codebase -- nothing here imports from it.
