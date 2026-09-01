"""
Document Chunking module for creating semantically rich text chunks with metadata.
Implements Hybrid Structure-Aware Heading Segmentation + Recursive Character Sub-chunking.
"""
import re
from typing import List, Dict, Any


class DocumentChunker:
    """
    Hybrid Structure-Aware and Recursive Character Chunker for NIE Biology materials.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.heading_pattern = re.compile(
            r"(\n(?:\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]+)", 
            re.MULTILINE
        )
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def create_chunks(self, pages_data: List[Dict[str, Any]], unit_name: str = "Unit 2") -> List[Dict[str, Any]]:
        """
        Splits page text into structure-aware, overlapping chunks with rich metadata tagging.
        """
        all_chunks = []
        global_chunk_count = 1

        for page in pages_data:
            text = page.get("content", "")
            page_num = page.get("page_number", 1)
            source_file = page.get("source_file", "Unknown")

            if not text.strip():
                continue

            # 1. Structure-Aware Segmentation on Section Headings
            sections = self._split_by_headings(text)

            for section in sections:
                sec_heading = section["heading"]
                sec_text = section["text"].strip()

                if not sec_text:
                    continue

                # 2. Sub-chunking: If section exceeds chunk_size, apply recursive splitting
                if len(sec_text) > self.chunk_size:
                    sub_texts = self._split_text_recursively(sec_text, self.separators)
                    for sub in sub_texts:
                        sub_clean = sub.strip()
                        if sub_clean:
                            all_chunks.append({
                                "chunk_id": f"{source_file}_p{page_num}_c{global_chunk_count}",
                                "text": sub_clean,
                                "metadata": {
                                    "source": source_file,
                                    "page": page_num,
                                    "unit": unit_name,
                                    "subject": "Biology",
                                    "section_heading": sec_heading,
                                    "char_length": len(sub_clean)
                                }
                            })
                            global_chunk_count += 1
                else:
                    all_chunks.append({
                        "chunk_id": f"{source_file}_p{page_num}_c{global_chunk_count}",
                        "text": sec_text,
                        "metadata": {
                            "source": source_file,
                            "page": page_num,
                            "unit": unit_name,
                            "subject": "Biology",
                            "section_heading": sec_heading,
                            "char_length": len(sec_text)
                        }
                    })
                    global_chunk_count += 1

        return all_chunks

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

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size or not separators:
            return [text]

        sep = separators[0]
        splits = text.split(sep) if sep else list(text)
        final_chunks = []
        current_chunk = ""

        for s in splits:
            piece = s + sep if sep else s
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
