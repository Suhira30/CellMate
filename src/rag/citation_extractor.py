"""
Citation Extractor Utility for CellMate RAG System.
Extracts, cleans, deduplicates, and formats source citations for UI display and API responses.
"""
from typing import List, Dict, Any


class CitationExtractor:
    """
    Utility for formatting and extracting rich metadata citations from retrieved RAG context chunks.
    """

    @staticmethod
    def extract_citations(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parses metadata from retrieved chunks and returns structured, deduplicated source objects.

        Returns:
            List of dicts:
                - source_file (str): e.g. "Unit 02-Chemical and cellular basis of life-English.pdf"
                - page_number (int/str): e.g. 14
                - section_heading (str): e.g. "2.3.1 Enzyme Inhibition"
                - doc_type (str): e.g. "resource_book"
                - markdown_badge (str): e.g. "`[NIE Resource Book | Page 14 | Sec: 2.3.1]`"
        """
        seen = set()
        citations = []

        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            source_file = meta.get("source", "NIE Resource Book")
            page_num = meta.get("page", "?")
            heading = meta.get("section_heading", "General")
            doc_type = meta.get("doc_type", "resource_book")

            # Unique key for deduplication
            key = (source_file, page_num, heading)
            if key in seen:
                continue
            seen.add(key)

            # Friendly title formatting
            if "Unit 02" in source_file or doc_type == "resource_book":
                friendly_doc = "NIE Resource Book"
            elif doc_type == "past_paper":
                friendly_doc = "A/L Past Paper"
            elif doc_type == "model_paper":
                friendly_doc = "A/L Model Paper"
            else:
                friendly_doc = source_file

            badge = f"`[{friendly_doc} | Page {page_num} | Sec: {heading}]`"

            citations.append({
                "source_file": source_file,
                "page_number": page_num,
                "section_heading": heading,
                "doc_type": doc_type,
                "markdown_badge": badge
            })

        return citations

    @staticmethod
    def format_citations_footer(citations: List[Dict[str, Any]]) -> str:
        """
        Formats citations into a clean Markdown footer block to append to LLM responses.
        """
        if not citations:
            return ""

        lines = ["\n\n---", "📚 **Sources & References (NIE A/L Syllabus):**"]
        for c in citations:
            lines.append(f"- {c['markdown_badge']} *{c['source_file']}*")

        return "\n".join(lines)

