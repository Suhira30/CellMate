"""
Vector Store Manager for CellMate RAG System.
Manages ChromaDB persistent vector store: collection lifecycle, chunk storage, similarity search, and stats.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from src.config import VECTORSTORE_DIR
from src.vector_db.embedder import EmbeddingEngine


class VectorStoreManager:
    """
    Manages a persistent ChromaDB vector collection for NIE Biology RAG retrieval.

    Responsibilities:
    - Create and connect to persistent ChromaDB collection at vectorstore/
    - Accept text chunks + metadata, embed via EmbeddingEngine, and store vectors
    - Query top-K semantically similar chunks by cosine similarity
    - Return collection stats for monitoring and debugging
    - Support full collection reset for re-ingestion experiments
    """

    def __init__(self, collection_name: str = "nie_biology_unit02"):
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(VECTORSTORE_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}   # Use cosine similarity for semantic search
        )
        self.embedder = EmbeddingEngine()

        print(f"✅ VectorStoreManager connected to collection '{collection_name}' "
              f"at {VECTORSTORE_DIR} ({self.collection.count()} chunks indexed)")

    def add_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 10) -> int:
        """
        Embeds and stores a list of text chunks with metadata into ChromaDB.

        Each chunk dict must contain:
            - chunk_id (str): unique identifier
            - text (str): the chunk content to embed
            - metadata (dict): page_number, source_file, strategy, char_length, etc.

        Returns the count of newly added chunks.
        """
        if not chunks:
            print("⚠️ add_chunks called with empty chunk list. Nothing to store.")
            return 0

        # Deduplicate: skip chunks already present in ChromaDB
        existing_ids = set(self.collection.get(ids=[c["chunk_id"] for c in chunks])["ids"])
        new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

        if not new_chunks:
            print("ℹ️ All provided chunks already exist in the collection. Skipping.")
            return 0

        print(f"📥 Adding {len(new_chunks)} new chunks to '{self.collection_name}'...")

        texts = [c["text"] for c in new_chunks]
        embeddings = self.embedder.embed_batch(texts, batch_size=batch_size)

        ids = [c["chunk_id"] for c in new_chunks]
        documents = [c["text"] for c in new_chunks]
        metadatas = [c.get("metadata", {}) for c in new_chunks]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        print(f"✅ Successfully stored {len(new_chunks)} chunks. "
              f"Collection total: {self.collection.count()} chunks.")
        return len(new_chunks)

    def query(
        self,
        query_text: str,
        top_k: int = 4,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs cosine similarity search for the top-K most relevant chunks.

        Args:
            query_text: The student's question or search string.
            top_k: Number of top results to return (default 4).
            where: Optional ChromaDB metadata filter dict (e.g. {"page_number": 5}).

        Returns:
            List of dicts, each containing:
                - text: chunk content
                - metadata: page, source, strategy
                - score: cosine similarity distance (lower = more similar)
        """
        total_in_coll = self.collection.count()
        if total_in_coll == 0:
            print(f"⚠️ Collection '{self.collection_name}' contains 0 chunks. Returning empty list.")
            return []

        query_embedding = self.embedder.embed_text(query_text)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": max(1, min(top_k, total_in_coll)),
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            query_kwargs["where"] = where

        raw_results = self.collection.query(**query_kwargs)

        results = []
        docs = raw_results.get("documents", [[]])[0]
        metas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            results.append({
                "text": doc,
                "metadata": meta,
                "score": round(dist, 6)
            })

        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns collection statistics for monitoring and diagnostics.
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "vectorstore_path": str(VECTORSTORE_DIR),
            "embedding_model": self.embedder.model,
            "similarity_metric": "cosine"
        }

    def reset_collection(self) -> None:
        """
        Deletes and recreates the ChromaDB collection.
        Use with caution — this permanently removes all stored embeddings.
        Useful for switching chunking strategies during Stage 3 retrieval experiments.
        """
        print(f"⚠️ Resetting collection '{self.collection_name}'...")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ Collection '{self.collection_name}' has been reset and is empty.")
