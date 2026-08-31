"""
Vector Store Manager using ChromaDB and Gemini Embeddings.
"""
import chromadb
from pathlib import Path
from typing import List, Dict, Any
from src.config import VECTORSTORE_DIR

class VectorStoreManager:
    def __init__(self, collection_name: str = "al_biology_unit2"):
        self.client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Add document chunks and their corresponding embeddings into ChromaDB.
        """
        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def query_similar(self, query_embedding: List[float], top_k: int = 4) -> Dict[str, Any]:
        """
        Query ChromaDB for top-K similar chunks based on query embedding vector.
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
