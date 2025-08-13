# utils/ingestion.py
from __future__ import annotations
import io
from typing import Tuple
from PIL import Image
from pypdf import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    out = []
    for page in reader.pages:
        try:
            out.append(page.extract_text() or "")
        except Exception:
            # keep going
            pass
    return "\n".join(out).strip()

def extract_text_from_image(file_bytes: bytes) -> str:
    """Try local OCR first (easyocr), else return empty string and let upstream LLM handle it."""
    try:
        import easyocr  # type: ignore
        reader = easyocr.Reader(['en'], gpu=False)
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        result = reader.readtext(np.array(img), detail=0)  # type: ignore
        return "\n".join(result).strip()
    except Exception:
        # OCR not available; upstream can decide to send image to LLM if supported
        return ""

def sniff_filetype(name: str) -> str:
    name = (name or "").lower()
    if name.endswith(".pdf"):
        return "pdf"
    if any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        return "image"
    return "binary"
