import io

from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader


def extract_text(raw_bytes: bytes, filename: str) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(raw_bytes))
        # doc.paragraphs only walks the top-level body flow, silently
        # skipping text inside floating text boxes -- common in templated
        # CVs that place dates in a text box next to each role. Walking
        # the full XML tree picks those up too, but naively (p.iter) would
        # also recurse into any nested w:p from a text box anchored inside
        # this one, double-counting that text when body.iter reaches the
        # nested w:p again on its own. So collect each paragraph's own text
        # by walking its children and stopping at (not into) a nested w:p --
        # that still crosses into wrappers like w:hyperlink, so linked text
        # (e.g. an emailed address rendered as a hyperlink run) isn't lost.
        def own_text(p):
            parts = []
            queue = list(p)
            while queue:
                el = queue.pop(0)
                if el.tag == qn("w:p"):
                    continue
                if el.tag == qn("w:t"):
                    parts.append(el.text or "")
                else:
                    queue[0:0] = list(el)
            return "".join(parts)

        paragraphs = [
            text for p in doc.element.body.iter(qn("w:p"))
            if (text := own_text(p)).strip()
        ]
        return "\n".join(paragraphs)

    raise ValueError(f"Unsupported file type: {filename}")
