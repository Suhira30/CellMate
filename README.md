# CellMate — Sri Lanka G.C.E. A/L Biology RAG System (BioGenie)

An AI-powered Retrieval-Augmented Generation (RAG) assistant for G.C.E. A/L Biology students in Sri Lanka.
Initial MVP focuses on **Unit 2: Chemical and Cellular Basis of Life** (English Medium).

## Directory Structure

```
RAG System/
├── data/
│   ├── raw/
│   │   ├── resource_book/      # Place NIE Biology Resource Book Unit 2 PDF here
│   │   ├── past_papers/        # Place Past Paper PDFs here
│   │   └── model_papers/       # Place Model Paper & Marking Scheme PDFs here
│   └── processed/              # Cleaned text & chunk cache
├── vectorstore/                # ChromaDB vector store directory
├── src/
│   ├── config.py               # Project configuration & environment setup
│   ├── ingestion/              # PDF extraction & text chunking modules
│   ├── vector_db/              # Gemini embedding & ChromaDB vector store
│   ├── rag/                    # Retriever & grounded Gemini generator
│   └── api/                    # FastAPI backend endpoints
├── frontend/                   # Streamlit web interface
└── requirements.txt            # Python dependencies
```

## Quick Start Setup

1. **Clone/Navigate to Project Directory**:

   ```bash
   cd "C:\Desktop\RAG System"
   ```

2. **Set up Virtual Environment**:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and insert your Google Gemini API key:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Place Resource Materials**:
   Add your Unit 2 NIE Resource Book PDF into `data/raw/resource_book/`.
