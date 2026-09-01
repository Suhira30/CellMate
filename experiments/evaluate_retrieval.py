"""
Chunking Strategy Retrieval Evaluation Framework — CellMate RAG System.

Evaluates all 6 chunking strategies against 15 NIE Biology A/L exam-style queries.
Measures:
  - Hit@1  : Was the top-1 result relevant?
  - Hit@K  : Was any of the top-K results relevant? (K=4)
  - MRR    : Mean Reciprocal Rank
  - Prec@K : Precision at K

Usage:
    python -m experiments.evaluate_retrieval
    python -m experiments.evaluate_retrieval --strategy hybrid_structure_recursive
    python -m experiments.evaluate_retrieval --skip-ingest   # Skip re-ingestion if already indexed
"""
import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings

from src.config import RESOURCE_BOOK_DIR, VECTORSTORE_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from src.ingestion.pdf_parser import PDFParser
from src.vector_db.embedder import EmbeddingEngine

# Import all 6 chunking strategies
from experiments.chunkers.character_chunker import FixedCharacterChunker
from experiments.chunkers.recursive_chunker import RecursiveCharacterChunker
from experiments.chunkers.token_chunker import TokenChunker
from experiments.chunkers.structure_chunker import StructureAwareChunker
from experiments.chunkers.semantic_chunker import SemanticChunker
from experiments.chunkers.hybrid_structure_recursive_chunker import HybridStructureRecursiveChunker


# ─── Strategy Registry ─────────────────────────────────────────────────────────

STRATEGIES = {
    "fixed_character": FixedCharacterChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
    "recursive_character": RecursiveCharacterChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
    "token_based": TokenChunker(max_tokens=120, token_overlap=20),
    "structure_aware": StructureAwareChunker(),
    # "semantic": SemanticChunker(target_size=CHUNK_SIZE), # Skipped due to Gemini Free Tier daily API quota limit
    "hybrid_structure_recursive": HybridStructureRecursiveChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP),
}

EVAL_QUERIES_PATH = Path(__file__).parent / "eval_queries.json"
TOP_K = 4


# ─── Helper Functions ──────────────────────────────────────────────────────────

def load_queries() -> List[Dict]:
    with open(EVAL_QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_relevant(chunk_text: str, expected_keywords: List[str]) -> bool:
    """Returns True if the chunk contains at least 2 of the expected keywords (case-insensitive)."""
    text_lower = chunk_text.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in text_lower)
    return hits >= 2


def compute_mrr(relevance_list: List[bool]) -> float:
    """Mean Reciprocal Rank for a single query result list."""
    for rank, is_rel in enumerate(relevance_list, 1):
        if is_rel:
            return 1.0 / rank
    return 0.0


def compute_precision_at_k(relevance_list: List[bool], k: int) -> float:
    """Precision@K for a single query result list."""
    top_k = relevance_list[:k]
    return sum(top_k) / k if top_k else 0.0


# ─── Ingestion per Strategy ────────────────────────────────────────────────────

def ingest_strategy_collection(
    strategy_name: str,
    chunker: Any,
    pages: List[Dict],
    embedder: EmbeddingEngine,
    chroma_client: chromadb.PersistentClient,
    force_reingest: bool = False
) -> int:
    """
    Chunks pages with the given strategy, embeds and stores in a dedicated ChromaDB collection.
    Collection name format: eval_{strategy_name}
    Reuses existing collections if present unless force_reingest is True.
    Returns total chunks stored.
    """
    collection_name = f"eval_{strategy_name}"

    # Reuse existing collection if populated
    if not force_reingest:
        try:
            existing = chroma_client.get_collection(collection_name)
            if existing.count() > 0:
                print(f"   ℹ️ Collection '{collection_name}' already exists ({existing.count()} chunks). Reusing existing embeddings.")
                return existing.count()
        except Exception:
            pass

    # Delete and recreate fresh collection if forcing reingestion
    try:
        chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    # Generate chunks using this strategy
    chunks = chunker.chunk_page.__func__(chunker, pages[0]) if hasattr(chunker, "chunk_page") else []

    # Handle different chunker interfaces
    all_chunks = []
    for page in pages:
        if hasattr(chunker, "chunk_page"):
            page_chunks = chunker.chunk_page(page)
        elif hasattr(chunker, "create_chunks"):
            page_chunks = chunker.create_chunks([page])
        else:
            continue
        all_chunks.extend(page_chunks)

    if not all_chunks:
        print(f"  ⚠️ Strategy '{strategy_name}' produced 0 chunks. Skipping.")
        return 0

    texts = [c.get("text", "") for c in all_chunks]
    embeddings = embedder.embed_batch(texts, batch_size=10)

    ids = [c.get("chunk_id", f"{strategy_name}_chunk_{i}") for i, c in enumerate(all_chunks)]
    metadatas = [c.get("metadata", {}) for c in all_chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    return len(all_chunks)


# ─── Retrieval Evaluation ──────────────────────────────────────────────────────

def evaluate_strategy(
    strategy_name: str,
    queries: List[Dict],
    embedder: EmbeddingEngine,
    chroma_client: chromadb.PersistentClient,
    top_k: int = TOP_K
) -> Dict[str, Any]:
    """
    Runs all evaluation queries against a strategy's ChromaDB collection.
    Returns per-strategy aggregated metrics.
    """
    collection_name = f"eval_{strategy_name}"
    try:
        collection = chroma_client.get_collection(collection_name)
    except Exception:
        return {"error": f"Collection '{collection_name}' not found. Run ingestion first."}

    hit_at_1_scores = []
    hit_at_k_scores = []
    mrr_scores = []
    prec_at_k_scores = []
    query_results = []

    for q in queries:
        query_embedding = embedder.embed_text(q["question"])
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "distances"]
        )

        docs = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]
        relevance = [is_relevant(doc, q["expected_keywords"]) for doc in docs]

        hit1 = relevance[0] if relevance else False
        hitk = any(relevance)
        mrr = compute_mrr(relevance)
        prec = compute_precision_at_k(relevance, top_k)

        hit_at_1_scores.append(hit1)
        hit_at_k_scores.append(hitk)
        mrr_scores.append(mrr)
        prec_at_k_scores.append(prec)

        query_results.append({
            "query_id": q["query_id"],
            "question": q["question"][:60] + "...",
            "hit@1": hit1,
            f"hit@{top_k}": hitk,
            "mrr": round(mrr, 3),
            f"prec@{top_k}": round(prec, 3),
            "top_result_preview": docs[0][:120] if docs else ""
        })

    n = len(queries)
    return {
        "strategy": strategy_name,
        "total_queries": n,
        "Hit@1": round(sum(hit_at_1_scores) / n * 100, 1),
        f"Hit@{top_k}": round(sum(hit_at_k_scores) / n * 100, 1),
        "MRR": round(sum(mrr_scores) / n, 3),
        f"Prec@{top_k}": round(sum(prec_at_k_scores) / n * 100, 1),
        "per_query": query_results
    }


# ─── Main Evaluation Runner ────────────────────────────────────────────────────

def run_evaluation(strategy_filter: str = None, skip_ingest: bool = False, force_reingest: bool = False):
    print("\n" + "=" * 75)
    print("🧪 CELLMATE CHUNKING STRATEGY RETRIEVAL EVALUATION")
    print("=" * 75)

    # Load eval queries
    queries = load_queries()
    print(f"📋 Loaded {len(queries)} evaluation queries from eval_queries.json\n")

    # Load and extract NIE Biology PDF pages
    target_pdf = RESOURCE_BOOK_DIR / "Unit 02-Chemical and cellular basis of life-English.pdf"
    if not target_pdf.exists():
        target_pdf = RESOURCE_BOOK_DIR / "Grade 12 Biology Resource Book English F11.pdf"

    if not target_pdf.exists():
        print("❌ NIE Resource Book PDF not found in data/raw/resource_book/")
        return

    print(f"📖 Extracting pages from: {target_pdf.name}...")
    parser = PDFParser(remove_headers_footers=True, enable_ocr=True)
    all_pages = parser.extract_text_from_pdf(target_pdf)
    pages = [p for p in all_pages if p.get("content", "").strip()]
    print(f"✅ Extracted {len(pages)} content pages.\n")

    # Init shared components
    embedder = EmbeddingEngine()
    chroma_client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR / "eval"),
        settings=Settings(anonymized_telemetry=False)
    )

    # Select strategies to evaluate
    strategies_to_run = {
        k: v for k, v in STRATEGIES.items()
        if strategy_filter is None or k == strategy_filter
    }

    # ── Ingestion Phase ────────────────────────────────────────────────────────
    if not skip_ingest:
        print("=" * 75)
        print("1️⃣  INGESTION PHASE: Chunking & Embedding all strategies...")
        print("=" * 75)
        for name, chunker in strategies_to_run.items():
            print(f"\n⚙️  Strategy: {name}")
            count = ingest_strategy_collection(name, chunker, pages, embedder, chroma_client, force_reingest=force_reingest)
            print(f"   ✅ Stored {count} chunks in collection 'eval_{name}'")
            time.sleep(1)
    else:
        print("⏭️  Skipping ingestion (--skip-ingest flag set)\n")

    # ── Retrieval Evaluation Phase ─────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("2️⃣  RETRIEVAL EVALUATION PHASE: Running 15 queries per strategy...")
    print("=" * 75)

    all_strategy_results = []
    for name in strategies_to_run:
        print(f"\n🔍 Evaluating: {name}")
        result = evaluate_strategy(name, queries, embedder, chroma_client)
        all_strategy_results.append(result)
        time.sleep(0.5)

    # ── Results Summary Table ─────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("📊 RETRIEVAL EVALUATION RESULTS SUMMARY")
    print("=" * 75)
    print(f"\n{'Strategy':<35} {'Hit@1':>6} {'Hit@4':>6} {'MRR':>7} {'Prec@4':>8}")
    print("-" * 75)

    best = max(all_strategy_results, key=lambda r: r.get("MRR", 0))

    for r in sorted(all_strategy_results, key=lambda x: x.get("MRR", 0), reverse=True):
        marker = " ⭐" if r["strategy"] == best["strategy"] else ""
        print(
            f"  {r['strategy']:<33} {r.get('Hit@1',''):>5}%  {r.get('Hit@4',''):>5}%  "
            f"{r.get('MRR',''):>6}  {r.get('Prec@4',''):>6}%{marker}"
        )

    print("-" * 75)
    print(f"\n🏆 Best Strategy by MRR: {best['strategy']} (MRR={best.get('MRR')})")

    # Save full results to JSON
    results_path = Path(__file__).parent / "retrieval_eval_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(all_strategy_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Full results saved to: {results_path}")
    print("=" * 75)


# ─── CLI Entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="CellMate Chunking Strategy Retrieval Evaluation"
    )
    arg_parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Evaluate a single strategy only (e.g. --strategy hybrid_structure_recursive)"
    )
    arg_parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip re-ingestion and use existing ChromaDB eval collections."
    )
    arg_parser.add_argument(
        "--force-reingest",
        action="store_true",
        help="Force re-ingest all collections even if they already exist."
    )
    args = arg_parser.parse_args()
    run_evaluation(strategy_filter=args.strategy, skip_ingest=args.skip_ingest, force_reingest=args.force_reingest)

