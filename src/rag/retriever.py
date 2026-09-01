"""
Vector Context Retriever for CellMate RAG System.
Handles query embedding, similarity search in ChromaDB, distance threshold filtering,
and source citation formatting.
"""
from typing import List, Dict, Any, Optional
from src.config import TOP_K, SIMILARITY_THRESHOLD
from src.vector_db.store_manager import VectorStoreManager


class VectorRetriever:
    """
    Production Context Retriever for G.C.E. A/L Biology RAG queries.

    Responsibilities:
    - Receive student question text
    - Query ChromaDB collection via VectorStoreManager
    - Filter results using Cosine Similarity Distance threshold
    - Format retrieved passages into prompt-ready context blocks with source citations
    """

    def __init__(
        self,
        store_manager: Optional[VectorStoreManager] = None,
        top_k: int = TOP_K,
        similarity_threshold: float = SIMILARITY_THRESHOLD
    ):
        self.store_manager = store_manager or VectorStoreManager(collection_name="nie_biology_unit02")
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold

    def retrieve(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        doc_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant NIE Biology chunks for a user question.

        Args:
            query_text: The student's question string.
            top_k: Optional override for number of chunks to fetch.
            doc_type_filter: Optional metadata filter ('resource_book', 'past_paper', 'model_paper').

        Returns:
            List of dicts containing:
                - text: chunk content
                - metadata: page, section_heading, source, doc_type
                - score: cosine distance
                - formatted_citation: e.g. "NIE Resource Book (Unit 2, Page 14, Section 2.3)"
        """
        k = top_k or self.top_k
        where_clause = {"doc_type": doc_type_filter} if doc_type_filter else None

        raw_results = self.store_manager.query(
            query_text=query_text,
            top_k=k,
            where=where_clause
        )

        filtered_results = []
        for res in raw_results:
            score = res.get("score", 1.0)
            meta = res.get("metadata", {})

            # In ChromaDB cosine distance: 0.0 = identical, 1.0 = orthogonal.
            # Keep chunks where distance <= threshold (lower score = higher similarity)
            if score <= self.similarity_threshold:
                source_file = meta.get("source", "NIE Resource Book")
                page_num = meta.get("page", "?")
                heading = meta.get("section_heading", "General")
                unit = meta.get("unit", "Unit 2")

                formatted_citation = f"[{source_file} | {unit} | Page {page_num} | Section: {heading}]"

                filtered_results.append({
                    "text": res["text"],
                    "metadata": meta,
                    "score": score,
                    "citation": formatted_citation
                })

        print(f"🔍 Retrieved {len(filtered_results)}/{len(raw_results)} chunks for query: '{query_text[:50]}...' "
              f"(Threshold <= {self.similarity_threshold})")

        return filtered_results

    def format_context_for_prompt(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into a clean context string to embed into the LLM system prompt.
        """
        if not retrieved_chunks:
            return "No relevant NIE Biology textbook passages found in the knowledge base."

        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            block = (
                f"--- CONTEXT BLOCK {idx} {chunk['citation']} ---\n"
                f"{chunk['text']}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)
