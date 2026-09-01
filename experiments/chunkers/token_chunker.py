"""
Strategy 3: Token-Based Chunking.
Splits text into fixed word/token limits (approx. 4 characters per token).
"""
from typing import List, Dict, Any


class TokenChunker:
    def __init__(self, max_tokens: int = 150, token_overlap: int = 25):
        self.max_tokens = max_tokens
        self.token_overlap = token_overlap

    def _estimate_tokens(self, text: str) -> List[str]:
        # Simple whitespace word tokenization
        return text.split()

    def chunk_page(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = page_data.get("content", "")
        words = self._estimate_tokens(text)
        if not words:
            return []

        chunks = []
        start = 0
        total_words = len(words)
        chunk_idx = 1

        while start < total_words:
            end = min(start + self.max_tokens, total_words)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "chunk_id": f"{page_data['source_file']}_p{page_data['page_number']}_token_{chunk_idx}",
                "text": chunk_text,
                "strategy": "token_based",
                "metadata": {
                    "source_file": page_data["source_file"],
                    "page_number": page_data["page_number"],
                    "token_count": len(chunk_words),
                    "char_length": len(chunk_text)
                }
            })

            if end == total_words:
                break
            start += self.max_tokens - self.token_overlap
            chunk_idx += 1

        return chunks

