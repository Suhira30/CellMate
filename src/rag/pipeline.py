"""
CellMate RAG Pipeline Orchestrator.
Combines VectorRetriever, RAGGenerator, and CitationExtractor into an end-to-end question answering engine.
"""
from typing import Dict, Any, Optional, List
from src.rag.retriever import VectorRetriever
from src.rag.generator import RAGGenerator
from src.rag.citation_extractor import CitationExtractor


class CellMateRAG:
    """
    Main RAG Pipeline Orchestrator for CellMate A/L Biology Assistant.

    Usage:
        rag = CellMateRAG()
        result = rag.answer_question("What is competitive enzyme inhibition?")
        print(result["answer"])
    """

    def __init__(
        self,
        retriever: Optional[VectorRetriever] = None,
        generator: Optional[RAGGenerator] = None,
        citation_extractor: Optional[CitationExtractor] = None
    ):
        self.retriever = retriever or VectorRetriever()
        self.generator = generator or RAGGenerator()
        self.citation_extractor = citation_extractor or CitationExtractor()

    def answer_question(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_type_filter: Optional[str] = None,
        include_citation_footer: bool = True
    ) -> Dict[str, Any]:
        """
        Executes full RAG workflow: Retrieve -> Synthesize -> Extract Citations -> Format Response.

        Args:
            query: The student's question string.
            top_k: Optional number of context chunks to fetch (default 4).
            doc_type_filter: Optional document filter ('resource_book', 'past_paper', etc.).
            include_citation_footer: Whether to append markdown source badges to the answer text.

        Returns:
            Dict containing:
                - query (str): original question
                - answer (str): full formatted answer text with optional footer
                - raw_answer (str): clean LLM answer without appended footer
                - citations (list): list of citation metadata dicts
                - is_grounded (bool): True if answer was synthesized from retrieved context
                - retrieved_chunks (list): raw context chunks returned by retriever
        """
        # Step 1: Retrieve context chunks
        chunks = self.retriever.retrieve(
            query_text=query,
            top_k=top_k,
            doc_type_filter=doc_type_filter
        )

        # Step 2: Extract citations
        citations = self.citation_extractor.extract_citations(chunks)

        # Step 3: Synthesize grounded response
        gen_result = self.generator.generate_response(
            query_text=query,
            retrieved_chunks=chunks
        )

        raw_answer = gen_result["answer"]
        is_grounded = gen_result.get("is_grounded", False)

        # Step 4: Append citation footer if grounded
        final_answer = raw_answer
        if include_citation_footer and is_grounded and citations:
            footer = self.citation_extractor.format_citations_footer(citations)
            final_answer += footer

        return {
            "query": query,
            "answer": final_answer,
            "raw_answer": raw_answer,
            "citations": citations,
            "is_grounded": is_grounded,
            "retrieved_chunks": chunks,
            "model_used": gen_result.get("model_used", "N/A")
        }

