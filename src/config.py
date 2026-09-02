"""
Central configuration module for CellMate (A/L BioGenie RAG System).
Reads from st.secrets (Streamlit Community Cloud) or .env (local development).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env for local development
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Streamlit Cloud secrets support — overrides .env when running on Streamlit Cloud
def _get_secret(key: str, default: str = "") -> str:
    """
    Read from st.secrets (cloud), .env, or .streamlit/secrets.toml (local fallback).
    """
    # 1. Try Streamlit runtime secrets if available
    try:
        import streamlit as st
        val = st.secrets.get(key, None)
        if val and val != "your_gemini_api_key_here":
            return str(val)
    except Exception:
        pass

    # 2. Try os.getenv / .env
    val = os.getenv(key, "")
    if val and val != "your_gemini_api_key_here":
        return val

    # 3. Fallback: parse .streamlit/secrets.toml directly if it exists
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key} =") or line.startswith(f'{key}='):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            parsed_val = parts[1].strip().strip('"').strip("'")
                            if parsed_val and parsed_val != "your_gemini_api_key_here":
                                return parsed_val
        except Exception:
            pass

    return default


# API Keys
GEMINI_API_KEY = _get_secret("GEMINI_API_KEY", "")

# Directory Paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESOURCE_BOOK_DIR = RAW_DATA_DIR / "resource_book"
PAST_PAPERS_DIR = RAW_DATA_DIR / "past_papers"
MODEL_PAPERS_DIR = RAW_DATA_DIR / "model_papers"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"

# Ensure essential directories exist
for dir_path in [RESOURCE_BOOK_DIR, PAST_PAPERS_DIR, MODEL_PAPERS_DIR, PROCESSED_DATA_DIR, VECTORSTORE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# RAG & Embedding Settings
EMBEDDING_MODEL = _get_secret("EMBEDDING_MODEL", "gemini-embedding-2")
LLM_MODEL = _get_secret("LLM_MODEL", "gemini-2.5-flash")
TOP_K = int(_get_secret("TOP_K", "4"))
SIMILARITY_THRESHOLD = float(_get_secret("SIMILARITY_THRESHOLD", "0.65"))

# Chunking Parameters
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def validate_config() -> bool:
    """
    Validates mandatory environment settings.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("⚠️ Warning: GEMINI_API_KEY is not set or using default placeholder in .env file.")
        return False
    return True
