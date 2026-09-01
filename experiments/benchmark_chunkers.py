"""
Benchmark & Comparison Suite for CellMate Chunking Strategies.
Evaluates all 5 chunking strategies against real pages extracted from:
`data/raw/resource_book/Grade 12 Biology Resource Book English F11.pdf`
"""
import time
from pathlib import Path
from typing import List, Dict, Any

from src.config import RESOURCE_BOOK_DIR
from src.ingestion.pdf_parser import PDFParser
from experiments.chunkers.character_chunker import FixedCharacterChunker
from experiments.chunkers.recursive_chunker import RecursiveCharacterChunker
from experiments.chunkers.token_chunker import TokenChunker
from experiments.chunkers.structure_chunker import StructureAwareChunker
from experiments.chunkers.semantic_chunker import SemanticChunker
from experiments.chunkers.hybrid_structure_recursive_chunker import HybridStructureRecursiveChunker

# Sample fallback text if PDF is not available
FALLBACK_PAGE = {
    "page_number": 14,
    "source_file": "Grade 12 Biology Resource Book English F11.pdf",
    "content": """
2.1 Chemical Basis of Life

2.1.1 Properties of Water Essential for Life
Water is the most abundant inorganic component of living organisms, constituting 70% to 95% of cellular mass. The unique physical and chemical properties of water stem from its polar covalent bonds and extensive intermolecular hydrogen bonding.

1. High Specific Heat Capacity: Water absorbs or loses a relatively large amount of heat energy with minimal temperature change (4.184 J/g°C). This buffers cell cytoplasm and aquatic ecosystems against rapid environmental thermal fluctuations.

2. High Latent Heat of Vaporization: Evaporative cooling (e.g. transpiration in plants and sweating in mammals) dissipates excess heat effectively because breaking hydrogen bonds requires significant thermal energy.

3. Cohesion and Surface Tension: Hydrogen bonding creates high cohesive forces among water molecules. This allows continuous water columns to be pulled upwards through xylem vessels against gravity.

2.3 Enzymes and Bioenergetics

2.3.1 Competitive and Non-Competitive Enzyme Inhibition
Enzymes lower the activation energy required for biochemical reactions. Inhibitors decrease enzyme activity:
- Competitive Inhibitors structurally resemble the substrate and bind reversibly to the active site, competing directly with substrate molecules. Increasing substrate concentration can reverse competitive inhibition.
- Non-Competitive Inhibitors bind to an allosteric site (a site other than the active site), altering the 3D tertiary structure of the enzyme and rendering the active site non-functional.
"""
}


def load_real_resource_book_pages(max_pages: int = 100) -> List[Dict[str, Any]]:
    """
    Extracts real pages from Unit 02-Chemical and cellular basis of life-English.pdf using PDFParser.
    """
    target_pdf = RESOURCE_BOOK_DIR / "Unit 02-Chemical and cellular basis of life-English.pdf"
    if not target_pdf.exists():
        target_pdf = RESOURCE_BOOK_DIR / "Grade 12 Biology Resource Book English F11.pdf"

    if not target_pdf.exists():
        print(f"⚠️ PDF not found at {target_pdf}. Using built-in sample text.")
        return [FALLBACK_PAGE]

    print(f"📖 Reading real PDF: {target_pdf.name} (Extracting all pages)...")
    parser = PDFParser(remove_headers_footers=True)
    all_pages = parser.extract_text_from_pdf(target_pdf)
    
    # Return all non-empty pages
    valid_pages = [p for p in all_pages if p.get("content", "").strip()]
    selected_pages = valid_pages[:max_pages]
    print(f"✅ Successfully loaded {len(selected_pages)} extracted pages from NIE Resource Book.\n")
    return selected_pages


def run_benchmark():
    pages = load_real_resource_book_pages(max_pages=100)
    total_characters = sum(len(p.get("content", "")) for p in pages)

    chunkers = {
        "1. Fixed Character": FixedCharacterChunker(chunk_size=600, chunk_overlap=100),
        "2. Recursive Character": RecursiveCharacterChunker(chunk_size=600, chunk_overlap=100),
        "3. Token-Based": TokenChunker(max_tokens=120, token_overlap=20),
        "4. Structure-Aware": StructureAwareChunker(max_chunk_size=600),
        "5. Semantic Paragraph": SemanticChunker(target_size=600),
        "6. Hybrid Structure-Recursive": HybridStructureRecursiveChunker(chunk_size=600, chunk_overlap=100)
    }

    print("=" * 85)
    print("🧬 CELLMATE CHUNKING BENCHMARK (REAL NIE RESOURCE BOOK DATA)")
    print("=" * 85)
    print(f"Input Data Source: Grade 12 Biology Resource Book English F11.pdf")
    print(f"Pages Evaluated: {len(pages)} pages | Total Characters: {total_characters:,} chars\n")

    results = []

    for name, chunker in chunkers.items():
        start_time = time.perf_counter()
        all_chunks = []
        for page in pages:
            chunks = chunker.chunk_page(page)
            all_chunks.extend(chunks)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        chunk_count = len(all_chunks)
        avg_len = sum(len(c["text"]) for c in all_chunks) / chunk_count if chunk_count > 0 else 0

        # Boundary integrity: ends cleanly with punctuation or newline
        clean_ends = sum(1 for c in all_chunks if c["text"].strip()[-1:] in [".", ":", "\n", "!"])
        boundary_integrity = (clean_ends / chunk_count * 100) if chunk_count > 0 else 0

        results.append({
            "name": name,
            "count": chunk_count,
            "avg_len": round(avg_len, 1),
            "integrity": round(boundary_integrity, 1),
            "speed_ms": round(elapsed_ms, 3)
        })

        preview = all_chunks[0]['text'][:85].replace("\n", " ") if chunk_count > 0 else "N/A"
        print(f"📌 [{name}]")
        print(f"   • Total Chunks Generated: {chunk_count}")
        print(f"   • Avg Chunk Length: {avg_len:.1f} chars")
        print(f"   • Boundary Integrity: {boundary_integrity:.1f}%")
        print(f"   • Total Benchmark Time: {elapsed_ms:.3f} ms")
        print(f"   • Sample Chunk Preview: \"{preview}...\"\n")

    print("=" * 85)
    print("📊 REAL DATA COMPARISON MATRIX SUMMARY")
    print("=" * 85)
    print(f"{'Strategy Name':<24} | {'Chunks':<8} | {'Avg Chars':<10} | {'Integrity %':<12} | {'Time (ms)':<10}")
    print("-" * 75)
    for r in results:
        print(f"{r['name']:<24} | {r['count']:<8} | {r['avg_len']:<10} | {r['integrity']:<12} | {r['speed_ms']:<10}")
    print("=" * 85)


if __name__ == "__main__":
    run_benchmark()
