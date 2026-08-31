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
│ • Parsers: `pdfplumber` + Custom Semantic Chunker (`src/ingestion/`)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Build Roadmap (Staged Progress Matrix)

### Stage 1: Foundation & Environment Setup

- [ ] **Task 1.1**: Initialize project environment (`.env`, Python venv, dependencies in `requirements.txt`).
- [ ] **Task 1.2**: Create directory structure (`data/raw/resource_book`, `data/processed/`, `vectorstore/`, `doc/`).
- [ ] **Task 1.3**: Configure `src/config.py` with environment variable loading and validation.

---

### Stage 2: Document Processing & Vector Indexing Pipeline

- [ ] **Task 2.1**: Implement PDF text parser in `src/ingestion/pdf_parser.py` extracting text and page numbers.
- [ ] **Task 2.2**: Build semantic recursive chunker in `src/ingestion/chunker.py` (500–1000 characters with 100-char overlap and metadata tagging).
- [ ] **Task 2.3**: Build ChromaDB store manager in `src/vector_db/store_manager.py` integrated with Gemini `gemini-embedding-2`.
- [ ] **Task 2.4**: Build batch ingestion pipeline script to populate ChromaDB from `data/raw/` PDFs.

---

### Stage 3: RAG Retrieval & Grounded Generation Engine

- [ ] **Task 3.1**: Build vector context retriever in `src/rag/retriever.py` with similarity score thresholding.
- [ ] **Task 3.2**: Refine grounded response generator in `src/rag/generator.py` enforcing strict NIE terminology rules.
- [ ] **Task 3.3**: Implement citation extraction logic to output exact source file names and page references.

---

### Stage 4: FastAPI REST Backend Endpoints

- [ ] **Task 4.1**: Define Pydantic request/response schemas in `src/api/main.py` (`QueryRequest`, `QueryResponse`, `SourceSnippet`).
- [ ] **Task 4.2**: Implement `POST /query` endpoint connecting backend API to RAG pipeline.
- [ ] **Task 4.3**: Implement `GET /health` and `GET /system/stats` diagnostic endpoints.

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
