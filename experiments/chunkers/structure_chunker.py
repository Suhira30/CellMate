"""
Strategy 4: Structure-Aware (Heading/Section) Chunking.
Parses NIE Biology section numbers (e.g. 2.1, 2.2, 2.3) and headings to split by logical topic boundaries.
"""
import re
from typing import List, Dict, Any


class StructureAwareChunker:
    def __init__(self, max_chunk_size: int = 800):
        self.max_chunk_size = max_chunk_size
        # Regex matching section headers like "2.1 Chemical Basis", "2.3.1 Enzyme Inhibition"
        self.section_pattern = re.compile(r"(\n(?:\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]+)")

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        if not text:
            return []

        # Split text on section headings
        sections = self.section_pattern.split("\n" + text)
        chunks = []
        chunk_idx = 1

        current_heading = "General Overview"
        buffer = ""

        for part in sections:
            part = part.strip()
            if not part:
                continue

            # Check if this part is a header
            if re.match(r"^\d+\.\d+(?:\.\d+)?\s+[A-Z]", part):
                if buffer:
                    chunks.append(self._create_chunk(buffer, current_heading, page_data, chunk_idx))
                    chunk_idx += 1
                    buffer = ""
                current_heading = part
                buffer = part + "\n"
            else:
                buffer += part + "\n"
                if len(buffer) >= self.max_chunk_size:
                    chunks.append(self._create_chunk(buffer, current_heading, page_data, chunk_idx))
                    chunk_idx += 1
                    buffer = ""

        if buffer.strip():
            chunks.append(self._create_chunk(buffer, current_heading, page_data, chunk_idx))

        return chunks

    def _create_chunk(self, text: str, section_title: str, page_data: Dict[str, Any], idx: int) -> Dict[str, Any]:
        return {
            "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_struct_{idx}",
            "text": text.strip(),
            "strategy": "structure_aware",
            "metadata": {
                "source_file": page_data["source_file"],
                "page_number": page_data["page_number"],
                "section_heading": section_title,
                "char_length": len(text.strip())
            }
        }

