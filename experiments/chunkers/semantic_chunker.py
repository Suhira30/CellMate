"""
Strategy 5: Semantic Sentence / Paragraph Chunking.
Splits document by paragraph boundaries and sentence clustering to maintain semantic cohesion.
"""
import re
from typing import List, Dict, Any


class SemanticChunker:
    def __init__(self, target_size: int = 600):
        self.target_size = target_size

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        if not text:
            return []

        # Split into paragraphs first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        chunk_idx = 1

        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > self.target_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_semantic_{chunk_idx}",
                    "text": chunk_text,
                    "strategy": "semantic_paragraph",
                    "metadata": {
                        "source_file": page_data["source_file"],
                        "page_number": page_data["page_number"],
                        "char_length": len(chunk_text)
                    }
                })
                chunk_idx += 1
                current_chunk = [p]
                current_len = p_len
            else:
                current_chunk.append(p)
                current_len += p_len

        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_semantic_{chunk_idx}",
                "text": chunk_text,
                "strategy": "semantic_paragraph",
                "metadata": {
                    "source_file": page_data["source_file"],
                    "page_number": page_data["page_number"],
                    "char_length": len(chunk_text)
                }
            })

        return chunks

