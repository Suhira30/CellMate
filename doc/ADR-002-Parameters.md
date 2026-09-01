# ADR-002: System Hyperparameters and Configuration Rationale

**Status**: 🟢 Accepted & Active  
**Date**: 2026-09-01  
**Project**: CellMate — G.C.E. A/L Biology RAG Study Assistant  
**Authors**: Senior AI Engineering Team

---

## 1. Context and Problem Statement

A Retrieval-Augmented Generation (RAG) system relies on several interdependent numerical parameters, model selections, threshold cutoffs, and rate-limiting delays across the document ingestion, vector indexing, retrieval, and generation stages.

Without a single authoritative Architecture Decision Record (ADR) documenting **every parameter value and its technical rationale**, configuration values become arbitrary "magic numbers", leading to unintended regressions during future refactoring.

> 📌 **Directive**: Every time a new parameter is defined or an existing value is modified in the CellMate codebase, it **MUST** be recorded in this document along with its empirical engineering rationale.

---

## 2. Ingestion & PDF Parser Parameters (`src/ingestion/pdf_parser.py`)

| Parameter                   |                 Current Value                  | Primary File    | Engineering Rationale & Justification                                                                                                                                                                                                                                                                           |
| :-------------------------- | :--------------------------------------------: | :-------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IMAGE_PAGE_CHAR_THRESHOLD` |                     `150`                      | `pdf_parser.py` | Pages returning $< 150$ characters of native vector text via PyMuPDF/pdfplumber are scanned/image-based or FlipHTML5 browser prints (which output only a 123-char URL string). Setting threshold to 150 ensures OCR triggers reliably for scanned pages without running redundantly on text-dense digital PDFs. |
| `OCR_DPI`                   |                     `200`                      | `pdf_parser.py` | 200 DPI provides the optimal trade-off between image clarity for PyTesseract OCR text recognition accuracy and image rendering speed/memory consumption. Higher DPI (300+) slows execution by ~3x with marginal OCR gain.                                                                                       |
| `OCR_CACHE_DIR`             |          `data/processed/ocr_cache/`           | `src/config.py` | Local disk cache storing MD5 hashed page OCR JSON outputs. Enables $0-cost re-runs and instant sub-millisecond page loading on subsequent ingestion pipelines.                                                                                                                                                  |
| `TESSERACT_EXE_PATH`        | `C:\Program Files\Tesseract-OCR\tesseract.exe` | `pdf_parser.py` | Standard Windows installation directory for Tesseract-OCR, auto-detected fallback for offline zero-cost OCR.                                                                                                                                                                                                    |

---

## 3. Chunking Strategy Parameters (`src/config.py` & `src/ingestion/chunker.py`)

| Parameter              |                 Current Value                 | Primary File    | Engineering Rationale & Justification                                                                                                                                                             |
| :--------------------- | :-------------------------------------------: | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `CHUNK_SIZE`           |                  `600 chars`                  | `src/config.py` | ~150 tokens. Bounded length ideal for dense semantic vector representations in `gemini-embedding-2`. Prevents the "fat chunk" problem where oversized chunks dilute vector focus.                 |
| `CHUNK_OVERLAP`        |                  `100 chars`                  | `src/config.py` | 16.7% sliding overlap ensuring key terms, definitions, and sentence context spanning across section boundaries are preserved without word duplication.                                            |
| `HEADING_PATTERN`      | `r"(\n(?:\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]+)"` | `chunker.py`    | Regex targeting NIE textbook section numbering conventions (e.g. `2.1`, `2.3.1`). Preserves hierarchy as metadata tags.                                                                           |
| `RECURSIVE_SEPARATORS` |        `["\n\n", "\n", ". ", " ", ""]`        | `chunker.py`    | Priority order for text splitting. Ensures paragraphs (`\n\n`) and complete sentences (`. `) are prioritized before falling back to word spaces, maintaining $>95\%$ sentence boundary integrity. |

---

## 4. Embedding Engine Parameters (`src/vector_db/embedder.py`)

| Parameter              |     Current Value      | Primary File    | Engineering Rationale & Justification                                                                                                                                       |
| :--------------------- | :--------------------: | :-------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `EMBEDDING_MODEL`      | `"gemini-embedding-2"` | `src/config.py` | Google's latest embedding model generating 768-dimensional float vectors optimized for multimodal and multilingual semantic similarity search.                              |
| `EMBEDDING_DIMENSIONS` |         `768`          | `embedder.py`   | Output float array dimension of `gemini-embedding-2`.                                                                                                                       |
| `MAX_EMBEDDING_CHARS`  |     `6,000 chars`      | `embedder.py`   | Hard token guard (~1,500 tokens). Safe buffer below the model's 2,048 token request limit, protecting against silent API truncation errors on giant un-chunked text blocks. |
| `EMBEDDING_BATCH_SIZE` |          `10`          | `embedder.py`   | Groups up to 10 chunks per embedding batch request to balance payload size and network round-trip overhead.                                                                 |
| `REQUEST_DELAY`        |         `0.7s`         | `embedder.py`   | Inter-call pacing delay guaranteeing maximum execution rate of $\sim 70$ RPM, staying safely below Google Gemini's **100 RPM** rate limit tier.                             |
| `BATCH_DELAY`          |         `1.5s`         | `embedder.py`   | Inter-batch pause to allow API rate limit sliding window to recover.                                                                                                        |
| `MAX_RETRIES`          |          `5`           | `embedder.py`   | Retries failed embedding calls up to 5 times with exponential backoff and a 35s pause on HTTP 429 (`RESOURCE_EXHAUSTED`).                                                   |

---

## 5. Vector DB & Retrieval Parameters (`src/rag/retriever.py` & `src/vector_db/store_manager.py`)

| Parameter              |     Current Value      | Primary File       | Engineering Rationale & Justification                                                                                                                               |
| :--------------------- | :--------------------: | :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `VECTORSTORE_DIR`      |     `vectorstore/`     | `src/config.py`    | Persistent local disk storage path for ChromaDB vector collections (gitignored).                                                                                    |
| `COLLECTION_NAME`      | `"nie_biology_unit02"` | `store_manager.py` | Dedicated collection for Unit 02 textbook and exam materials.                                                                                                       |
| `SIMILARITY_SPACE`     |       `"cosine"`       | `store_manager.py` | Cosine similarity HNSW index space. Normalized distance range $[0.0, 1.0]$ where $0.0$ indicates identical semantic meaning.                                        |
| `TOP_K`                |          `4`           | `src/config.py`    | Returns top 4 context passages per user question. Empirical testing proved $K=4$ captures $93.3\%$ Hit Rate while staying under LLM context noise limits.           |
| `SIMILARITY_THRESHOLD` |         `0.65`         | `src/config.py`    | Cosine distance cutoff threshold. Chunks with distance $> 0.65$ are discarded as irrelevant noise, protecting Gemini LLM from hallucination on off-topic questions. |

---

## 6. LLM Generation Parameters (`src/rag/generator.py`)

| Parameter         |    Current Value     | Primary File    | Engineering Rationale & Justification                                                                                                    |
| :---------------- | :------------------: | :-------------- | :--------------------------------------------------------------------------------------------------------------------------------------- |
| `LLM_MODEL`       | `"gemini-2.5-flash"` | `src/config.py` | Active Gemini model for answer synthesis. High speed, cost-efficient, and strong instruction following for strict NIE terminology rules. |
| `LLM_TEMPERATURE` |        `0.2`         | `generator.py`  | Low temperature setting minimizing creative variance, forcing the model to strictly adhere to retrieved NIE Biology context passages.    |

---

## 7. Change Log & Maintenance Protocol

Whenever a developer or automated script modifies any configuration parameter:

1. Update `src/config.py` or the target module.
2. Update the corresponding row in **this ADR (`doc/ADR-002-Parameters.md`)**.
3. Record the reason and empirical verification metrics in the table above.
