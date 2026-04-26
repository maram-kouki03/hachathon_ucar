"""
utils/extractor.py — Extraction de texte depuis PDF, image, Excel, CSV.
"""
import tempfile
import os

import fitz          # PyMuPDF
import pytesseract
from PIL import Image
import pandas as pd


def extract_text(file) -> str:
    """
    Reçoit un objet Streamlit UploadedFile.
    Retourne le texte extrait sous forme de chaîne.
    Lève une exception en cas d'erreur.
    """
    suffix = file.name.split(".")[-1].lower()
    file.seek(0)  # s'assurer qu'on est au début

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(file.read())
        path = tmp.name

    try:
        # ── PDF ──────────────────────────────────────────────────────────────
        if suffix == "pdf":
            text = ""
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
            doc.close()
            # Si PDF scanné sans couche texte → fallback OCR sur la 1ère page
            if len(text.strip()) < 50:
                page = fitz.open(path)[0]
                pix = page.get_pixmap(dpi=200)
                img_path = path + "_ocr.png"
                pix.save(img_path)
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img, lang="fra+eng")
                os.unlink(img_path)
            return text

        # ── IMAGES ───────────────────────────────────────────────────────────
        elif suffix in ("png", "jpg", "jpeg"):
            img = Image.open(path)
            return pytesseract.image_to_string(img, lang="fra+eng")

        # ── EXCEL ────────────────────────────────────────────────────────────
        elif suffix in ("xlsx", "xls"):
            # Lire tous les onglets et les concaténer
            xl = pd.ExcelFile(path)
            parts = []
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                parts.append(f"=== Onglet : {sheet} ===\n{df.to_string(index=False)}")
            return "\n\n".join(parts)

        # ── CSV ──────────────────────────────────────────────────────────────
        elif suffix == "csv":
            # Essaye plusieurs encodages
            for enc in ("utf-8", "latin-1", "cp1252"):
                try:
                    df = pd.read_csv(path, encoding=enc)
                    return df.to_string(index=False)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(path, encoding="utf-8", errors="replace").to_string(index=False)

        else:
            return "Unsupported file"

    finally:
        try:
            os.unlink(path)
        except Exception:
            pass