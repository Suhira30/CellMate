# System Architecture & Implementation Plan Roadmap

**Product**: A/L BioGenie (Sri Lanka G.C.E. A/L Biology RAG System - Unit 2 MVP)

---

## 1. System Architecture Overview

### 1.1 Tech Stack Specification

```
┌────────────────────────────────────────────────────────────────────────┐
│ FRONTEND LAYER                                                        │
│ • Streamlit / Web UI (Python 3.10+, Tailwind CSS Components)          │
│ • Interactive Chat Stream, Quick Prompt Pills, Source Inspector Drawer │
└────────────────────────────────────────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│ BACKEND API LAYER (FastAPI)                                            │
│ • POST /query (Query Processing)                                       │
│ • GET /health (API & Vector Store Health Check)                        │
│ • GET /system/stats (Indexed Documents & Chunk Statistics)             │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ RAG GENERATOR & RETRIEVAL ENGINE                                       │
│ • Retriever: Top-K Cosine Similarity Search via ChromaDB               │
│ • LLM Engine: Google Gemini API (gemini-1.5-flash / gemini-1.5-pro)   │
│ • Guardrails: Strict NIE System Instructions & Citation Enforcer       │
└────────────────────────────────────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ VECTOR DATABASE & DATA PIPELINE                                        │
│ • Vector DB: Persistent ChromaDB (`vectorstore/`)                      │
│ • Embeddings: Google Gemini `gemini-embedding-2`                       │
│ • Parsers: PyMuPDF / pdfplumber + $0-Cost PyTesseract OCR (`src/ingestion/`) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Build Roadmap (Staged Progress Matrix)

### Stage 1: Foundation & Environment Setup

- [x] **Task 1.1**: Initialize project environment (`.env`, Python venv, dependencies in `requirements.txt`).
- [x] **Task 1.2**: Create directory structure (`data/raw/resource_book`, `data/processed/`, `vectorstore/`, `doc/`).
- [x] **Task 1.3**: Configure `src/config.py` with environment variable loading and validation.

---

### Stage 2: Document Processing & Vector Indexing Pipeline

- [x] **Task 2.1**: Implement multi-engine PDF text & table parser in `src/ingestion/pdf_parser.py` (PyMuPDF / pdfplumber for digital text + $0-cost Local PyTesseract OCR with Gemini 1.5 Flash Vision fallback for image/FlipHTML5 PDFs + local disk caching in `data/processed/ocr_cache/`).
- [x] **Task 2.2**: Build 6 modular chunking strategies in `experiments/chunkers/` (Fixed, Recursive, Token, Structure-Aware, Semantic, and Hybrid Structure-Recursive) and configure `src/ingestion/chunker.py`.
- [x] **Task 2.2.1**: Build evaluation inspector (`experiments/inspect_pdf_extraction.py`) and benchmarking suite (`experiments/benchmark_chunkers.py`) comparing chunk counts, average sizes, and sentence boundary integrity % across all 66 extracted NIE textbook pages.
- [x] **Task 2.3**: Build ChromaDB store manager in `src/vector_db/store_manager.py` (collection creation, add/query/delete operations, persistent storage).
- [x] **Task 2.3.1**: Build Embedding Engine wrapper in `src/vector_db/embedder.py` using `gemini-embedding-2` (`text-embedding` API, 768-dimension vectors, batch-safe with rate limiting).
- [x] **Task 2.4**: Build batch ingestion pipeline in `src/ingestion/ingest.py` orchestrating: extract → chunk → **embed** → store into ChromaDB.

> 💡 **Evaluation Note**: Chunking strategy final selection follows a Two-Phase methodology:
>
> 1. _Static Data Prep_: Measuring chunk size and boundary integrity.
> 2. _Retrieval Ground Truth_: Measuring Retrieval Hit Rate & Precision@K during Stage 3 vector search testing before locking in final production choice.

---

### Stage 3: RAG Retrieval & Grounded Generation Engine

- [x] **Task 3.1**: Build vector context retriever in `src/rag/retriever.py` with similarity score thresholding, metadata filtering, and formatted prompt context generation.
- [x] **Task 3.2**: Refine grounded response generator in `src/rag/generator.py` enforcing strict NIE terminology rules, temperature=0.2, dual SDK support, and model fallback retries.
- [x] **Task 3.3**: Implement citation extraction logic (`src/rag/citation_extractor.py`), pipeline orchestrator (`src/rag/pipeline.py`), and verification script (`experiments/test_rag_pipeline.py`).

---

### Stage 4: FastAPI REST Backend Endpoints

- [x] **Task 4.1**: Define Pydantic request/response schemas and FastAPI REST endpoints in `src/api/main.py` (`POST /api/v1/query`, `GET /api/v1/health`, `GET /api/v1/system/stats`).
- [x] **Task 4.2**: Implement interactive Streamlit Web UI application in `src/ui/app.py` with chat stream, quick prompt pills, sidebar configuration, and expandable NIE textbook source citation drawer.

---

### Stage 5: Web Frontend & User Interface

- [ ] **Task 5.1**: Enhance Streamlit web interface in `frontend/app.py` matching the Design Brief layout.
- [ ] **Task 5.2**: Add quick revision prompt starter chips (_Properties of Water_, _Enzyme Inhibition_, _Protein Structure_).
- [ ] **Task 5.3**: Build Source Inspector slide-out panel for displaying page extracts and confidence scores.
- [ ] **Task 5.4**: Add Unit 2 sub-topic navigation sidebar filter.

---

### Stage 6: Testing, Quality Assurance & Verification

- [ ] **Task 6.1**: Unit test chunking and page metadata preservation (`tests/test_chunker.py`).
- [ ] **Task 6.2**: Test RAG generation grounding and out-of-syllabus term prevention.
- [ ] **Task 6.3**: Verify end-to-end user query flow from web frontend to Gemini API response.

---

## 3. Verification Plan

### Automated Tests

- Run `pytest` for chunking and API endpoint verification:
  ```bash
  python -m pytest tests/
  ```

### Manual Verification

- Test sample queries:
  1. _"What are the physical properties of water according to the NIE Resource Book?"_
  2. _"Explain competitive vs non-competitive enzyme inhibition with examples."_
- Verify that source citations show exact page references from `NIE Biology Resource Book Unit 2`.
