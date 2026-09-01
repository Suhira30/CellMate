"""
Inspection script to view extracted page contents from official NIE Unit 02 Biology Resource Book PDF
before chunking is applied.
"""
import json
from pathlib import Path
from src.config import RESOURCE_BOOK_DIR
from src.ingestion.pdf_parser import PDFParser


def inspect_extracted_pdf():
    target_pdf = RESOURCE_BOOK_DIR / "Unit 02-Chemical and cellular basis of life-English.pdf"
    if not target_pdf.exists():
        target_pdf = RESOURCE_BOOK_DIR / "Grade 12 Biology Resource Book English F11.pdf"

    if not target_pdf.exists():
        print(f"❌ PDF not found in {RESOURCE_BOOK_DIR}")
        return

    print("=" * 85)
    print(f"🔍 INSPECTING EXTRACTED CONTENT FROM: {target_pdf.name}")
    print("=" * 85)

    parser = PDFParser(remove_headers_footers=True)
    all_pages = parser.extract_text_from_pdf(target_pdf)
    valid_pages = [p for p in all_pages if p.get("content", "").strip()]

    print(f"✅ Total Pages Extracted with Content: {len(valid_pages)}\n")

    # Display inspection summary for first 3 non-empty pages
    for i, page in enumerate(valid_pages[:3], 1):
        print("-" * 85)
        print(f"📄 EXTRACTED PAGE #{page['page_number']} | Character Length: {len(page['content'])}")
        print("-" * 85)
        print("CONTENT PREVIEW:")
        print(page['content'][:600])
        if len(page['content']) > 600:
            print("\n... [content truncated for terminal preview] ...")

        if page.get("tables"):
            print(f"\n📊 Extracted Tables ({len(page['tables'])} table(s) found):")
            for t_idx, tbl in enumerate(page['tables'], 1):
                print(f"Table #{t_idx}:\n{tbl}\n")
        print("\n")

    # Save a sample JSON export of extracted pages to experiments/extracted_sample.json
    output_sample_path = Path(__file__).parent / "extracted_sample.json"
    sample_data = valid_pages[:5]
    with open(output_sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Exported sample extracted pages JSON to: {output_sample_path}")
    print("=" * 85)


if __name__ == "__main__":
    inspect_extracted_pdf()
