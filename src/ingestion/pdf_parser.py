"""
PDF Extraction module for NIE Biology Resource Books and Past Papers.
"""
import pypdf
from pathlib import Path
from typing import List, Dict, Any

class PDFParser:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file page by page with metadata.
        """
        pages_data = []
        reader = pypdf.PdfReader(str(pdf_path))
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_data.append({
                    "page_number": i + 1,
                    "content": text.strip(),
                    "source_file": pdf_path.name
                })
        return pages_data
