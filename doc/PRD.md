# Product Requirements Document (PRD)

## A/L BioGenie — Sri Lanka G.C.E. A/L Biology RAG Assistant

---

### 1. Document Overview

- **Product Name**: A/L BioGenie
- **Target Audience**: G.C.E. Advanced Level (A/L) Biology Students & Educators in Sri Lanka (English Medium)
- **Initial MVP Scope**: **Unit 2: Chemical and Cellular Basis of Life**
- **Version**: 1.0.0
- **Status**: Active MVP

---

### 2. Product Objectives & Target Audience

#### 2.1 Problem Statement

Sri Lankan G.C.E. A/L Biology students face significant challenges preparing for national examinations:

1. **Strict Marking Schemes**: Answers must adhere strictly to exact terms and definitions established in the official **National Institute of Education (NIE) Biology Resource Book**. Generic AI models (e.g. ChatGPT, Claude) frequently hallucinate or use foreign syllabus terms (e.g., AP / IB / Cambridge Biology specs) which result in lost exam marks.
2. **Dense Learning Material**: Finding precise page-level citations across large resource books, past papers, and model marking schemes is time-consuming.

#### 2.2 Product Vision

A/L BioGenie provides an intelligent, grounded RAG (Retrieval-Augmented Generation) assistant that guarantees zero-hallucination, NIE-compliant answers accompanied by instant page-level citations for every response.

---

### 3. Functional Requirements

#### 3.1 Document Ingestion Pipeline (`src/ingestion/`)

- **PDF Extraction**: Parse NIE Biology Resource Book Unit 2 PDF, past papers, and marking scheme PDFs using PyPDF2 / pdfplumber.
- **Text Chunking**: Chunk text into semantic paragraphs (500–1000 characters) preserving page numbers and source metadata.

#### 3.2 Vector Database & Embeddings (`src/vector_db/`)

- **Vector Store**: ChromaDB local vector storage.
- **Embedding Model**: Google Gemini API Embeddings (`models/gemini-embedding-2` or `gemini-embedding-001`).
- **Metadata Tagging**: Store page numbers, chapter headers, document types (Resource Book vs Past Paper).

#### 3.3 Grounded RAG Generator (`src/rag/`)

- **Retriever**: Top-K semantic similarity search matching student queries against ChromaDB vector index.
- **Strict Prompting**: Enforce system prompt prohibiting out-of-syllabus terms and mandating exact NIE definitions.
- **LLM Engine**: Google Gemini API (`gemini-1.5-pro` / `gemini-1.5-flash`).

#### 3.4 API & UI Interfaces (`src/api/` & `frontend/`)

- **FastAPI Backend**: REST endpoints for query processing (`POST /query`) and health monitoring (`GET /health`).
- **Web Frontend**: Interactive UI providing chat interface, example practice prompt chips (e.g. _Properties of Water_, _Enzyme Inhibition_, _Protein Structure_), and source citation drawers.

---

### 4. Non-Functional Requirements

1. **Response Grounding & Accuracy**: 100% of generated biological facts must be supported by retrieved NIE context chunks.
2. **Response Time**: Query response latency < 3.0 seconds.
3. **Accessibility**: WCAG 2.1 AA compliant UI design tokens, font contrast, and screen reader labels.

---

### 5. Future Scope & Roadmap

- **Phase 2**: Ingestion of Units 3 through 10 (Plant & Animal Form/Function, Genetics, Ecology).
- **Phase 3**: Past Paper Structured Question Grading Assistant with automated marking scheme breakdown.
- **Phase 4**: Multi-lingual support (Sinhala & Tamil Medium resource books).
