"""
Unit tests for all 5 chunking experiment strategies.
"""
from experiments.chunkers.character_chunker import FixedCharacterChunker
from experiments.chunkers.recursive_chunker import RecursiveCharacterChunker
from experiments.chunkers.token_chunker import TokenChunker
from experiments.chunkers.structure_chunker import StructureAwareChunker
from experiments.chunkers.semantic_chunker import SemanticChunker
from experiments.chunkers.hybrid_structure_recursive_chunker import HybridStructureRecursiveChunker
from experiments.benchmark_chunkers import FALLBACK_PAGE


def test_fixed_character_chunker():
    chunker = FixedCharacterChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "fixed_character"
    assert "source_file" in chunks[0]["metadata"]


def test_recursive_character_chunker():
    chunker = RecursiveCharacterChunker(chunk_size=300, chunk_overlap=50)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "recursive_character"


def test_token_chunker():
    chunker = TokenChunker(max_tokens=50, token_overlap=10)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "token_based"


def test_structure_aware_chunker():
    chunker = StructureAwareChunker(max_chunk_size=400)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "structure_aware"


def test_semantic_chunker():
    chunker = SemanticChunker(target_size=400)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "semantic_paragraph"


def test_hybrid_structure_recursive_chunker():
    chunker = HybridStructureRecursiveChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_page(FALLBACK_PAGE)
    assert len(chunks) > 0
    assert chunks[0]["strategy"] == "hybrid_structure_recursive"
    assert "section_heading" in chunks[0]["metadata"]


