"""
Document Chunking module for creating semantically rich text chunks with metadata.
"""
from typing import List, Dict, Any

class DocumentChunker:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_chunks(self, pages_data: List[Dict[str, Any]], unit_name: str = "Unit 2") -> List[Dict[str, Any]]:
        """
        Splits page text into overlapping chunks with rich metadata tagging.
        """
        chunks = []
        chunk_id = 0

        for page in pages_data:
            text = page["content"]
            page_num = page["page_number"]
            source_file = page["source_file"]

            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                chunks.append({
                    "chunk_id": f"{source_file}_p{page_num}_c{chunk_id}",
                    "text": chunk_text,
                    "metadata": {
                        "source": source_file,
                        "page": page_num,
                        "unit": unit_name,
                        "subject": "Biology"
                    }
                })
                chunk_id += 1
                start += (self.chunk_size - self.chunk_overlap)

        return chunks
