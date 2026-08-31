"""
Retriever module for handling vector search queries and similarity threshold filtering.
"""
from typing import List, Dict, Any
from src.vector_db.store_manager import VectorStoreManager
from src.config import TOP_K, SIMILARITY_THRESHOLD

class Retriever:
    def __init__(self, store_manager: VectorStoreManager):
        self.store_manager = store_manager

    def retrieve_relevant_chunks(self, query_text: str, query_embedding: List[float]) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for a given query vector.
        """
        results = self.store_manager.query_similar(query_embedding, top_k=TOP_K)
        
        retrieved_chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            
            for doc, meta in zip(docs, metas):
                retrieved_chunks.append({
                    "text": doc,
                    "metadata": meta
                })
                
        return retrieved_chunks
