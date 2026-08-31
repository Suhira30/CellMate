import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Directory Paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESOURCE_BOOK_DIR = RAW_DATA_DIR / "resource_book"
PAST_PAPERS_DIR = RAW_DATA_DIR / "past_papers"
MODEL_PAPERS_DIR = RAW_DATA_DIR / "model_papers"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

# RAG & Embedding Settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
TOP_K = int(os.getenv("TOP_K", "4"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

# Chunking Parameters
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
