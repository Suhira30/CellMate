"""
Strategy 2: Recursive Character Chunking.
Recursively splits on paragraph, line, and sentence boundaries to preserve context.
"""
from typing import List, Dict, Any


class RecursiveCharacterChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        if not text:
            return []

        raw_chunks = self._split_text_recursively(text, self.separators)
        chunks = []

        for idx, chunk_text in enumerate(raw_chunks, 1):
            if chunk_text.strip():
                chunks.append({
                    "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_rec_{idx}",
                    "text": chunk_text.strip(),
                    "strategy": "recursive_character",
                    "metadata": {
                        "source_file": page_data["source_file"],
                        "page_number": page_data["page_number"],
                        "char_length": len(chunk_text.strip())
                    }
                })
        return chunks

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size or not separators:
            return [text]

        separator = separators[0]
        splits = text.split(separator) if separator else list(text)
        final_chunks = []
        current_chunk = ""

        for s in splits:
            piece = s + separator if separator else s
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                if len(piece) > self.chunk_size and len(separators) > 1:
                    sub_splits = self._split_text_recursively(s, separators[1:])
                    final_chunks.extend(sub_splits)
                    current_chunk = ""
                else:
                    current_chunk = piece

        if current_chunk:
            final_chunks.append(current_chunk)

        return final_chunks

