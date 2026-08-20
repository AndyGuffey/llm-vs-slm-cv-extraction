import io

from docx import Document
from pypdf import PdfReader


def extract_text(raw_bytes: bytes, filename: str) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(raw_bytes))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {filename}")
