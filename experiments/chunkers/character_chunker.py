"""
Strategy 1: Fixed Character-Level Chunking.
Splits text into strict character windows regardless of sentence boundaries.
"""
from typing import List, Dict, Any


class FixedCharacterChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)
        chunk_idx = 1

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end]

            chunks.append({
                "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_fixed_{chunk_idx}",
                "text": chunk_text,
                "strategy": "fixed_character",
                "metadata": {
                    "source_file": page_data["source_file"],
                    "page_number": page_data["page_number"],
                    "start_char": start,
                    "end_char": end,
                    "char_length": len(chunk_text)
                }
            })

            if end == text_len:
                break
            start += self.chunk_size - self.chunk_overlap
            chunk_idx += 1

        return chunks

