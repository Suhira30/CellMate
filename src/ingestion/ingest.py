"""
Batch Ingestion Pipeline for CellMate RAG System.
Orchestrates the full Extract → Chunk → Embed → Store pipeline.

Usage:
    python -m src.ingestion.ingest                          # Ingest all PDFs from data/raw/
    python -m src.ingestion.ingest --reset                  # Reset collection and re-ingest
    python -m src.ingestion.ingest --stats                  # View collection stats only
"""
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

from src.config import (
    RESOURCE_BOOK_DIR, PAST_PAPERS_DIR, MODEL_PAPERS_DIR,
    CHUNK_SIZE, CHUNK_OVERLAP
)
from src.ingestion.pdf_parser import PDFParser
from src.ingestion.chunker import DocumentChunker
from src.vector_db.store_manager import VectorStoreManager


# ─── Document Source Configuration ────────────────────────────────────────────

DOCUMENT_SOURCES = [
    {
        "dir": RESOURCE_BOOK_DIR,
        "unit": "Unit 2 - Chemical & Cellular Basis of Life",
        "doc_type": "resource_book"
    },
    {
        "dir": PAST_PAPERS_DIR,
        "unit": "A/L Biology Past Paper",
        "doc_type": "past_paper"
    },
    {
        "dir": MODEL_PAPERS_DIR,
        "unit": "A/L Biology Model Paper",
        "doc_type": "model_paper"
    },
]


# ─── Pipeline Functions ────────────────────────────────────────────────────────

def discover_pdfs(source_config: Dict) -> List[Path]:
    """Returns all PDF files found in a source directory."""
    directory = Path(source_config["dir"])
    if not directory.exists():
        return []
    return sorted(directory.glob("*.pdf"))


def ingest_pdf(
    pdf_path: Path,
    unit_name: str,
    doc_type: str,
    parser: PDFParser,
    chunker: DocumentChunker,
    store: VectorStoreManager
) -> Dict[str, Any]:
    """
    Runs the full Extract → Chunk → Embed → Store pipeline for a single PDF file.
    Returns a summary dict of ingestion statistics.
    """
    print(f"\n{'─' * 70}")
    print(f"📄 Ingesting: {pdf_path.name}")
    print(f"   Type: {doc_type}  |  Unit: {unit_name}")
    print(f"{'─' * 70}")

    start_time = time.time()

    # Step 1: Extract
    print("1️⃣  Extracting text from PDF...")
    pages = parser.extract_text_from_pdf(pdf_path)
    valid_pages = [p for p in pages if p.get("content", "").strip()]
    print(f"   ✅ Extracted {len(valid_pages)} content pages.")

    if not valid_pages:
        print("   ⚠️ No extractable content found. Skipping this file.")
        return {"file": pdf_path.name, "pages": 0, "chunks": 0, "stored": 0, "skipped": True}

    # Step 2: Chunk
    print("2️⃣  Chunking extracted text...")
    chunks = chunker.create_chunks(valid_pages, unit_name=unit_name)

    # Attach doc_type to each chunk's metadata for retrieval filtering
    for chunk in chunks:
        chunk["metadata"]["doc_type"] = doc_type

    print(f"   ✅ Generated {len(chunks)} chunks (avg {sum(c['metadata']['char_length'] for c in chunks) // max(len(chunks), 1)} chars each).")

    # Step 3: Embed & Store
    print("3️⃣  Embedding and storing chunks in ChromaDB...")
    stored = store.add_chunks(chunks)

    elapsed = round(time.time() - start_time, 2)
    print(f"   ✅ Stored {stored} new chunks in {elapsed}s.")

    return {
        "file": pdf_path.name,
        "pages": len(valid_pages),
        "chunks_generated": len(chunks),
        "chunks_stored": stored,
        "elapsed_seconds": elapsed,
        "skipped": False
    }


def run_ingestion_pipeline(reset: bool = False) -> None:
    """
    Runs the full ingestion pipeline across all document sources.
    If reset=True, clears the ChromaDB collection before ingesting.
    """
    print("\n" + "=" * 70)
    print("🚀 CELLMATE RAG INGESTION PIPELINE STARTING")
    print("=" * 70)

    # Initialize components
    parser = PDFParser(remove_headers_footers=True, enable_ocr=True)
    chunker = DocumentChunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    store = VectorStoreManager(collection_name="nie_biology_unit02")

    if reset:
        print("\n⚠️  --reset flag detected. Clearing existing ChromaDB collection...")
        store.reset_collection()

    # Discover all PDFs across all source directories
    all_results = []
    total_pdfs_found = 0

    for source in DOCUMENT_SOURCES:
        pdfs = discover_pdfs(source)
        if not pdfs:
            print(f"\n📁 {source['dir'].name}/: No PDFs found. Skipping.")
            continue

        print(f"\n📁 {source['dir'].name}/: Found {len(pdfs)} PDF(s)")
        total_pdfs_found += len(pdfs)

        for pdf_path in pdfs:
            result = ingest_pdf(
                pdf_path=pdf_path,
                unit_name=source["unit"],
                doc_type=source["doc_type"],
                parser=parser,
                chunker=chunker,
                store=store
            )
            all_results.append(result)

    # ─── Final Summary Report ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("📊 INGESTION PIPELINE SUMMARY")
    print("=" * 70)

    total_pages = sum(r["pages"] for r in all_results)
    total_generated = sum(r["chunks_generated"] for r in all_results if not r.get("skipped"))
    total_stored = sum(r["chunks_stored"] for r in all_results if not r.get("skipped"))
    total_time = sum(r.get("elapsed_seconds", 0) for r in all_results)

    print(f"  PDFs Processed     : {total_pdfs_found}")
    print(f"  Pages Extracted    : {total_pages}")
    print(f"  Chunks Generated   : {total_generated}")
    print(f"  Chunks Stored (New): {total_stored}")
    print(f"  Total Time         : {round(total_time, 2)}s")

    print("\n📦 ChromaDB Collection Stats:")
    stats = store.get_stats()
    for k, v in stats.items():
        print(f"  {k:<25}: {v}")

    print("\n✅ Ingestion pipeline complete. ChromaDB is ready for retrieval!")
    print("=" * 70)


def show_stats() -> None:
    """Prints current ChromaDB collection stats without running ingestion."""
    store = VectorStoreManager(collection_name="nie_biology_unit02")
    stats = store.get_stats()
    print("\n📦 Current ChromaDB Collection Stats:")
    for k, v in stats.items():
        print(f"  {k:<25}: {v}")


# ─── CLI Entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CellMate RAG Batch Ingestion Pipeline"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the ChromaDB collection before ingesting (use for re-ingestion)."
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current ChromaDB collection stats without running ingestion."
    )
    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        run_ingestion_pipeline(reset=args.reset)

