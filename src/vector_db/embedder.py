"""
Embedding Engine for CellMate RAG System.
Uses Google Gemini gemini-embedding-2 to generate 768-dimensional semantic vectors.
Includes batch-safe processing, token guard, and retry logic.
"""
import time
from typing import List
from src.config import GEMINI_API_KEY, EMBEDDING_MODEL

MAX_EMBEDDING_CHARS = 6000  # ~1500 tokens — safe buffer below 2048 token limit

try:
    from google import genai
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False


class EmbeddingEngine:
    """
    Wrapper around Google Gemini Embedding API (gemini-embedding-2).
    Produces 768-dimensional semantic float vectors for text chunks.
    Handles batching, token guard, and API retry with exponential backoff.
    """

    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is not set in your .env file. "
                "Please add your Gemini API key to c:\\Desktop\\RAG System\\.env"
            )

        self.client = None
        self.use_legacy = False

        if HAS_NEW_GENAI:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.use_legacy = False
        elif HAS_LEGACY_GENAI:
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            self.client = legacy_genai
            self.use_legacy = True
        else:
            raise ImportError(
                "Neither 'google-genai' nor 'google-generativeai' is installed. "
                "Please run: pip install -r requirements.txt"
            )

        self.model = EMBEDDING_MODEL

    def _guard_chunk(self, text: str) -> str:
        """
        Truncates text to MAX_EMBEDDING_CHARS to prevent API token limit errors.
        Logs a warning if truncation occurs.
        """
        if len(text) > MAX_EMBEDDING_CHARS:
            print(
                f"⚠️ Embedding guard: chunk truncated from {len(text)} "
                f"to {MAX_EMBEDDING_CHARS} chars to avoid token limit."
            )
            return text[:MAX_EMBEDDING_CHARS]
        return text

    def embed_text(self, text: str, retries: int = 5) -> List[float]:
        """
        Embeds a single text string into a 768-dimensional float vector.
        Retries up to `retries` times with exponential backoff and quota window handling.
        """
        text = self._guard_chunk(text)

        for attempt in range(1, retries + 1):
            try:
                if self.use_legacy:
                    result = self.client.embed_content(
                        model=self.model,
                        content=text
                    )
                    return result["embedding"]
                else:
                    result = self.client.models.embed_content(
                        model=self.model,
                        contents=text
                    )
                    return result.embeddings[0].values
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait = 35
                    print(f"⚠️ Rate limit / Quota exceeded (429). Pausing {wait}s for API window reset... (Attempt {attempt}/{retries})")
                else:
                    wait = 2 ** attempt
                    print(f"⚠️ Embedding attempt {attempt}/{retries} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)

        raise RuntimeError(
            f"Embedding failed after {retries} retries. "
            "Check your GEMINI_API_KEY and internet connection."
        )

    def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Embeds a list of text strings in batches.
        Respects the 100 RPM API rate limit by pacing calls with a 0.7s delay.
        Returns a list of 768-dim embedding vectors in the same order as input.
        """
        all_embeddings = []
        total = len(texts)

        for i in range(0, total, batch_size):
            batch = texts[i: i + batch_size]
            print(f"🔢 Embedding batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} "
                  f"({len(batch)} chunks)...")
            for text in batch:
                vec = self.embed_text(text)
                all_embeddings.append(vec)
                time.sleep(0.7)  # 0.7s delay guarantees max ~85 RPM, avoiding the 100 RPM cap

            # Additional pause between batches
            if i + batch_size < total:
                time.sleep(1.5)

        return all_embeddings

