"""
Strategy 6: Hybrid Structure-Aware + Recursive Character Chunking.
Combines section heading detection (structure-aware) with recursive character fallback 
for sections exceeding target chunk size.
"""
import re
from typing import List, Dict, Any
from experiments.chunkers.recursive_chunker import RecursiveCharacterChunker


class HybridStructureRecursiveChunker:
    """
    Hybrid chunker that first parses document structure (headings/sections),
    then recursively sub-chunks large sections while preserving context metadata.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.recursive_chunker = RecursiveCharacterChunker(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        # Patterns matching NIE section headings e.g. "2.1 Chemical Basis", "2.1.1 Properties of Water"
        self.heading_pattern = re.compile(
            r"(\n(?:\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]+)", 
            re.MULTILINE
        )

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        if not text:
            return []

        # 1. Structure-Aware Segmentation (Heading Detection)
        sections = self._split_by_headings(text)
        final_chunks = []
        global_idx = 1

        for sec_idx, section in enumerate(sections, 1):
            sec_heading = section["heading"]
            sec_text = section["text"].strip()

            if not sec_text:
                continue

            # 2. Sub-chunking: If section exceeds chunk_size, apply Recursive Character Chunking
            if len(sec_text) > self.chunk_size:
                sub_page_data = {
                    "content": sec_text,
                    "source_file": page_data["source_file"],
                    "page_number": page_data["page_number"]
                }
                sub_chunks = self.recursive_chunker.chunk_page(sub_page_data)

                for sub in sub_chunks:
                    final_chunks.append({
                        "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_hybrid_{global_idx}",
                        "text": sub["text"],
                        "strategy": "hybrid_structure_recursive",
                        "metadata": {
                            "source_file": page_data["source_file"],
                            "page_number": page_data["page_number"],
                            "section_heading": sec_heading,
                            "char_length": len(sub["text"]),
                            "is_subchunked": True
                        }
                    })
                    global_idx += 1
            else:
                final_chunks.append({
                    "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_hybrid_{global_idx}",
                    "text": sec_text,
                    "strategy": "hybrid_structure_recursive",
                    "metadata": {
                        "source_file": page_data["source_file"],
                        "page_number": page_data["page_number"],
                        "section_heading": sec_heading,
                        "char_length": len(sec_text),
                        "is_subchunked": False
                    }
                })
                global_idx += 1

        return final_chunks

    def _split_by_headings(self, text: str) -> List[Dict[str, str]]:
        parts = self.heading_pattern.split("\n" + text)
        sections = []
        current_heading = "General Content"
        buffer = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if re.match(r"^\d+\.\d+(?:\.\d+)?\s+[A-Z]", part):
                if buffer.strip():
                    sections.append({"heading": current_heading, "text": buffer.strip()})
                current_heading = part
                buffer = part + "\n"
            else:
                buffer += part + "\n"

        if buffer.strip():
            sections.append({"heading": current_heading, "text": buffer.strip()})

        return sections

