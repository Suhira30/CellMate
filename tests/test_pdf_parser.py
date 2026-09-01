"""
Unit tests for PDFParser module (Task 2.1).
"""
import pytest
from pathlib import Path
from src.ingestion.pdf_parser import PDFParser


def test_pdf_parser_initialization():
    parser = PDFParser(remove_headers_footers=True)
    assert parser.remove_headers_footers is True


def test_clean_text_hyphenation_and_whitespace():
    parser = PDFParser(remove_headers_footers=True)
    raw = "Biological bio-\nlogical molecules are import-\nant for cell-\nular functions."
    cleaned = parser._clean_text(raw)
    assert "biological" in cleaned
    assert "important" in cleaned
    assert "cellular" in cleaned


def test_clean_text_header_footer_stripping():
    parser = PDFParser(remove_headers_footers=True)
    raw = "G.C.E. (A/L) BIOLOGY RESOURCE BOOK\nUnit 02: Chemical and Cellular Basis of Life\nWater is essential for life.\nNational Institute of Education"
    cleaned = parser._clean_text(raw)
    assert "G.C.E. (A/L) BIOLOGY RESOURCE BOOK" not in cleaned
    assert "Water is essential for life." in cleaned


def test_table_to_markdown_conversion():
    parser = PDFParser()
    table = [
        ["Property", "Water", "Methane"],
        ["Specific Heat", "High (4.184 J/g°C)", "Low"],
        ["Boiling Point", "100°C", "-161°C"]
    ]
    md = parser._table_to_markdown(table)
    assert "| Property | Water | Methane |" in md
    assert "| --- | --- | --- |" in md
    assert "| Specific Heat | High (4.184 J/g°C) | Low |" in md


def test_fliphtml5_detection():
    parser = PDFParser()
    flip_text = "8/31/26 Grade 12 Biology Resource Book https://online.fliphtml5.com/fpvjb/xjsk/#p=1 14/244"
    assert parser._is_fliphtml_or_scanned(flip_text) is True
    normal_text = "2.1 Chemical Basis of Life. Water is the most abundant inorganic component of living organisms."
    assert parser._is_fliphtml_or_scanned(normal_text) is False


