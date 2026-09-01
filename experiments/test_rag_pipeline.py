"""
Interactive Test Script for CellMate RAG Pipeline (Stage 3 Verification).

Usage:
    python -m experiments.test_rag_pipeline
    python -m experiments.test_rag_pipeline --query "What is the lock and key model of enzyme action?"
"""
import argparse
import sys
from src.rag.pipeline import CellMateRAG

DEFAULT_SAMPLE_QUERIES = [
    "What are the unique properties of water that make it essential for life?",
    "Explain the difference between competitive and non-competitive enzyme inhibition.",
    "What is the structure of a phospholipid bilayer in cell membranes?",
    "What elements are essential for living organisms according to NIE Biology?"
]


def run_test(query: str = None):
    print("\n" + "=" * 75)
    print("🧬 CELLMATE RAG PIPELINE VERIFICATION")
    print("=" * 75)

    rag = CellMateRAG()

    queries_to_test = [query] if query else DEFAULT_SAMPLE_QUERIES

    for q in queries_to_test:
        print(f"\n❓ Question: {q}")
        print("-" * 75)

        result = rag.answer_question(q)

        print(f" Status    : Grounded = {result['is_grounded']} | Chunks Used = {len(result['retrieved_chunks'])}")
        print(f" Model     : {result.get('model_used', 'N/A')}")
        print(f" Citations : {len(result['citations'])} source reference(s) extracted")
        print("\n📝 Response Output:\n")
        print(result["answer"])
        print("\n" + "=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test CellMate RAG Pipeline")
    parser.add_argument("--query", type=str, default=None, help="Single query question to test")
    args = parser.parse_args()

    run_test(query=args.query)

