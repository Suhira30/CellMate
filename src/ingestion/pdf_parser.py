"""
PDF Extraction module for NIE Biology Resource Books and Past Papers using PyMuPDF / pdfplumber
and $0-Cost Local PyTesseract OCR (with Gemini Vision API fallback) for image-based/FlipHTML5 printed PDFs.
"""
import os
import re
import json
import io
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# Import Gemini API & Config for optional cloud fallback
from src.config import GEMINI_API_KEY, PROCESSED_DATA_DIR, LLM_MODEL

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False


class PDFParser:
    """
    Robust, $0-Cost Local PDF text & table parser designed for NIE Biology Resource Books.
    Uses PyMuPDF / pdfplumber for digital text and Local PyTesseract OCR for scanned/FlipHTML5 image PDFs.
    """

    def __init__(self, remove_headers_footers: bool = True, enable_ocr: bool = True):
        self.remove_headers_footers = remove_headers_footers
        self.enable_ocr = enable_ocr
        self.ocr_cache_dir = PROCESSED_DATA_DIR / "ocr_cache"
        self.ocr_cache_dir.mkdir(parents=True, exist_ok=True)

        self.genai_client = None
        self.use_legacy_genai = False

        if HAS_NEW_GENAI and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
                self.use_legacy_genai = False
            except Exception:
                pass
        elif HAS_LEGACY_GENAI and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                legacy_genai.configure(api_key=GEMINI_API_KEY)
                self.genai_client = legacy_genai.GenerativeModel(LLM_MODEL)
                self.use_legacy_genai = True
            except Exception:
                pass

        # Patterns matching NIE resource book page headers & footers
        self.header_footer_patterns = [
            re.compile(r"G\.C\.E\.\s*\(A/L\)\s*BIOLOGY\s*RESOURCE\s*BOOK", re.IGNORECASE),
            re.compile(r"NATIONAL\s+INSTITUTE\s+OF\s+EDUCATION", re.IGNORECASE),
            re.compile(r"UNIT\s+0?2\s*[:\-]?\s*CHEMICAL\s+AND\s+CELLULAR\s+BASIS\s+OF\s+LIFE", re.IGNORECASE),
            re.compile(r"^\s*\d+\s*$", re.MULTILINE),  # Standalone page numbers
        ]

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""

        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

        if self.remove_headers_footers:
            for pattern in self.header_footer_patterns:
                text = pattern.sub("", text)

        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def _table_to_markdown(self, table: List[List[Optional[str]]]) -> str:
        if not table or not any(table):
            return ""

        cleaned_table = []
        for row in table:
            if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                continue
            cleaned_row = [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
            cleaned_table.append(cleaned_row)

        if not cleaned_table:
            return ""

        num_cols = max(len(row) for row in cleaned_table)
        headers = cleaned_table[0] + [""] * (num_cols - len(cleaned_table[0]))

        header_str = "| " + " | ".join(headers) + " |"
        separator_str = "| " + " | ".join(["---"] * num_cols) + " |"

        body_rows = []
        for row in cleaned_table[1:]:
            padded_row = row + [""] * (num_cols - len(row))
            body_rows.append("| " + " | ".join(padded_row) + " |")

        return "\n".join([header_str, separator_str] + body_rows)

    def _is_image_page(self, text: str) -> bool:
        clean = text.strip()
        if len(clean) < 150:
            return True
        return False

    def _get_page_image_bytes(self, pdf_path: Path, page_num: int) -> Optional[bytes]:
        """
        Extracts high-resolution PNG page image bytes using PyMuPDF (fitz), pdfplumber, or pypdf.
        """
        # 1. PyMuPDF (fitz)
        if HAS_FITZ:
            try:
                doc = fitz.open(str(pdf_path))
                if page_num <= len(doc):
                    page = doc[page_num - 1]
                    pix = page.get_pixmap(dpi=200)
                    return pix.tobytes("png")
            except Exception:
                pass

        # 2. pypdf image XObject extraction
        if HAS_PYPDF:
            try:
                reader = pypdf.PdfReader(str(pdf_path))
                if page_num <= len(reader.pages):
                    page = reader.pages[page_num - 1]
                    if len(page.images) > 0:
                        return page.images[0].data
            except Exception:
                pass

        # 3. pdfplumber image render
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(str(pdf_path)) as pdf:
                    if page_num <= len(pdf.pages):
                        page = pdf.pages[page_num - 1]
                        img_render = page.to_image(resolution=150)
                        buf = io.BytesIO()
                        img_render.original.save(buf, format="PNG")
                        return buf.getvalue()
            except Exception:
                pass

        return None

    def _ocr_page_image(self, image_bytes: bytes, page_num: int, pdf_name: str) -> str:
        """
        Runs Local PyTesseract OCR ($0 Cost), falling back to Gemini Vision API with model retries.
        Result is cached locally in data/processed/ocr_cache/.
        """
        cache_key = hashlib.md5(f"{pdf_name}_p{page_num}".encode("utf-8")).hexdigest()
        cache_file = self.ocr_cache_dir / f"{cache_key}.json"

        # Check local disk cache
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("text", "")
            except Exception:
                pass

        extracted_text = ""

        # Strategy 1: Local PyTesseract OCR ($0 Cost, 100% Offline)
        if HAS_TESSERACT:
            try:
                print(f"💻 Running Local PyTesseract OCR ($0 Cost) for {pdf_name} (Page {page_num})...")
                img = Image.open(io.BytesIO(image_bytes))
                extracted_text = pytesseract.image_to_string(img, lang="eng").strip()
            except Exception as e:
                print(f"⚠️ Local PyTesseract OCR notice on page {page_num}: {e}")

        # Strategy 2: Cloud Gemini Vision OCR Fallback with Model Candidate Retries
        if not extracted_text and self.genai_client:
            prompt = (
                "You are an expert OCR system for Sri Lanka G.C.E. A/L Biology NIE Resource Books. "
                "Extract all text, section titles (e.g. 2.1 Chemical Basis of Life, 2.1.1 Properties of Water), "
                "and data tables from this page image. Format tables as Markdown."
            )
            candidate_models = [LLM_MODEL, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]

            for model_name in candidate_models:
                clean_model = model_name.replace("models/", "")
                try:
                    print(f"🌐 Running Cloud Gemini Vision OCR ({clean_model}) for {pdf_name} (Page {page_num})...")
                    if self.use_legacy_genai:
                        img = Image.open(io.BytesIO(image_bytes))
                        response = self.genai_client.generate_content([prompt, img])
                        extracted_text = response.text.strip() if response.text else ""
                    else:
                        response = self.genai_client.models.generate_content(
                            model=clean_model,
                            contents=[
                                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                                prompt
                            ]
                        )
                        extracted_text = response.text.strip() if response.text else ""
                    
                    if extracted_text:
                        break
                except Exception as e:
                    print(f"⚠️ Vision OCR attempt with model '{clean_model}' on page {page_num} failed: {e}")

        # Cache extracted result if non-empty
        if extracted_text.strip():
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"pdf": pdf_name, "page": page_num, "text": extracted_text}, f, indent=2)

        return extracted_text

    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

        # Try PyMuPDF (fitz) native extraction first
        if HAS_FITZ:
            try:
                res = self._extract_with_fitz(pdf_path)
                if res:
                    return res
            except Exception as e:
                print(f"⚠️ PyMuPDF extraction notice for {pdf_path.name}: {e}. Trying pdfplumber...")

        if HAS_PDFPLUMBER:
            try:
                res = self._extract_with_pdfplumber(pdf_path)
                if res:
                    return res
            except Exception as e:
                print(f"⚠️ pdfplumber extraction notice for {pdf_path.name}: {e}. Trying pypdf...")

        return self._extract_with_pypdf(pdf_path)

    def _extract_with_fitz(self, pdf_path: Path) -> List[Dict[str, Any]]:
        pages_data = []
        doc = fitz.open(str(pdf_path))
        for i, page in enumerate(doc):
            page_num = i + 1
            raw_text = page.get_text() or ""
            cleaned_text = self._clean_text(raw_text)

            if self.enable_ocr and self._is_image_page(cleaned_text):
                image_bytes = self._get_page_image_bytes(pdf_path, page_num)
                if image_bytes:
                    ocr_text = self._ocr_page_image(image_bytes, page_num, pdf_path.name)
                    if ocr_text.strip():
                        cleaned_text = self._clean_text(ocr_text)

            # Preserve native text if OCR returned empty or failed
            if cleaned_text.strip() or raw_text.strip():
                final_content = cleaned_text.strip() if cleaned_text.strip() else raw_text.strip()
                pages_data.append({
                    "page_number": page_num,
                    "content": final_content,
                    "tables": [],
                    "source_file": pdf_path.name,
                    "source_path": str(pdf_path.resolve())
                })
        return pages_data

    def _extract_with_pdfplumber(self, pdf_path: Path) -> List[Dict[str, Any]]:
        pages_data = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                raw_text = page.extract_text(layout=False) or ""
                cleaned_text = self._clean_text(raw_text)

                if self.enable_ocr and self._is_image_page(cleaned_text):
                    image_bytes = self._get_page_image_bytes(pdf_path, page_num)
                    if image_bytes:
                        ocr_text = self._ocr_page_image(image_bytes, page_num, pdf_path.name)
                        if ocr_text.strip():
                            cleaned_text = self._clean_text(ocr_text)

                tables_md = []
                extracted_tables = page.extract_tables()
                for tbl in extracted_tables:
                    tbl_md = self._table_to_markdown(tbl)
                    if tbl_md:
                        tables_md.append(tbl_md)

                combined_content = cleaned_text if cleaned_text.strip() else raw_text.strip()
                if tables_md:
                    combined_content += "\n\n### Extracted Tables:\n" + "\n\n".join(tables_md)

                if combined_content.strip():
                    pages_data.append({
                        "page_number": page_num,
                        "content": combined_content.strip(),
                        "tables": tables_md,
                        "source_file": pdf_path.name,
                        "source_path": str(pdf_path.resolve())
                    })
        return pages_data

    def _extract_with_pypdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        if not HAS_PYPDF:
            raise ImportError("Please install dependencies: pip install -r requirements.txt")
        pages_data = []
        reader = pypdf.PdfReader(str(pdf_path))
        for i, page in enumerate(reader.pages):
            page_num = i + 1
            raw_text = page.extract_text() or ""
            cleaned_text = self._clean_text(raw_text)

            if self.enable_ocr and self._is_image_page(cleaned_text):
                image_bytes = self._get_page_image_bytes(pdf_path, page_num)
                if image_bytes:
                    ocr_text = self._ocr_page_image(image_bytes, page_num, pdf_path.name)
                    if ocr_text.strip():
                        cleaned_text = self._clean_text(ocr_text)

            combined_content = cleaned_text if cleaned_text.strip() else raw_text.strip()

            if combined_content.strip():
                pages_data.append({
                    "page_number": page_num,
                    "content": combined_content.strip(),
                    "tables": [],
                    "source_file": pdf_path.name,
                    "source_path": str(pdf_path.resolve())
                })
        return pages_data
