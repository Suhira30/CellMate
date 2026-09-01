"""
Unit tests for DocumentChunker module (Task 2.2).
"""
import pytest
from src.ingestion.chunker import DocumentChunker


def test_document_chunker_basic():
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    sample_pages = [{
        "page_number": 1,
        "source_file": "Unit_2_Test.pdf",
        "content": "2.1 Chemical Basis of Life\nWater is essential for life with high heat capacity.\n\n2.2 Biomolecules\nProteins consist of amino acid polymers linked by peptide bonds."
    }]
    chunks = chunker.create_chunks(sample_pages, unit_name="Unit 2")
    assert len(chunks) >= 2
    assert "source" in chunks[0]["metadata"]
    assert chunks[0]["metadata"]["source"] == "Unit_2_Test.pdf"
    assert chunks[0]["metadata"]["unit"] == "Unit 2"
    assert "section_heading" in chunks[0]["metadata"]


def test_document_chunker_empty_page():
    chunker = DocumentChunker()
    sample_pages = [{"page_number": 2, "source_file": "Empty.pdf", "content": "   "}]
    chunks = chunker.create_chunks(sample_pages)
    assert len(chunks) == 0

