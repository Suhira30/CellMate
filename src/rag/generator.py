"""
Grounded RAG Response Generator for CellMate RAG System.
Synthesizes syllabus-compliant A/L Biology responses using Gemini API
grounded strictly in retrieved NIE Resource Book context passages.
"""
import time
from typing import List, Dict, Any, Optional
from src.config import GEMINI_API_KEY, LLM_MODEL

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False


# ─── System Instructions for Sri Lankan A/L Biology ───────────────────────────

SYSTEM_INSTRUCTION = """You are CellMate, an expert AI Study Assistant for Sri Lanka G.C.E. Advanced Level Biology (Unit 02: Chemical and Cellular Basis of Life).

Your task is to answer the student's question strictly using ONLY the provided NIE Resource Book and Past Paper context snippets below.

STRICT OPERATING RULES:
1. STRICT ADHERENCE: Use exact NIE Biology Resource Book definitions, scientific terms, and keywords.
2. NO HALLUCINATION: Do NOT invent facts or use international syllabus terminology (e.g. AP/IB Biology) not present in the Sri Lankan A/L syllabus.
3. CONTEXT GROUNDING: Base every statement directly on the provided context passages. If the context does not contain enough information to answer fully, state clearly what is supported by the textbook and what is unverified.
4. CITATIONS: Reference the specific source file, page number, and section for key facts.
5. RESPONSE STRUCTURE:
   • 📌 **Core Answer / Definition**: Direct, concise summary matching A/L marking scheme expectations.
   • 🔬 **Detailed Explanation**: Comprehensive biological explanation using exact NIE terminology.
   • 📖 **NIE Textbook References**: Bulleted list of source files, pages, and sections used.
"""

MODEL_CANDIDATES = [
    LLM_MODEL,          # Default from config: gemini-2.5-flash
    "gemini-3.6-flash", # Google's recommended replacement for retired models
    "gemini-2.5-flash", # Latest stable Flash model
    "gemini-2.5-pro",   # Pro fallback for complex queries
]


class RAGGenerator:
    """
    Grounded Response Generator for CellMate RAG System.
    Connects to Gemini API with dual SDK support, model fallback retries,
    temperature control (0.2), and strict grounding enforcement.
    """

    def __init__(self, temperature: float = 0.2):
        self.temperature = temperature
        self.client = None
        self.use_legacy = False

        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            print("⚠️ Warning: GEMINI_API_KEY is not configured in .env file.")
            return

        if HAS_NEW_GENAI:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            self.use_legacy = False
        elif HAS_LEGACY_GENAI:
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            self.client = legacy_genai
            self.use_legacy = True

    def generate_response(
        self,
        query_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        context_str: str = ""
    ) -> Dict[str, Any]:
        """
        Synthesizes a grounded answer from retrieved context passages.

        Args:
            query_text: The student's question string.
            retrieved_chunks: List of retrieved chunk dicts from VectorRetriever.
            context_str: Pre-formatted context string (optional).

        Returns:
            Dict containing:
                - answer (str): Structured, syllabus-compliant response text
                - sources (list): Extracted list of unique source citations
                - is_grounded (bool): True if answer was synthesized from retrieved context
                - chunks_used (int): Number of context blocks provided to the LLM
        """
        # Guard: If no relevant context chunks are provided, return zero-hallucination notice
        if not retrieved_chunks:
            return {
                "answer": (
                    "⚠️ **No Relevant NIE Biology Context Found**\n\n"
                    "I could not find relevant passages in the NIE Unit 02 Resource Book "
                    "matching your question. Please try rephrasing your question using "
                    "standard Sri Lankan A/L Biology terminology."
                ),
                "sources": [],
                "is_grounded": False,
                "chunks_used": 0
            }

        # Build formatted context block if not provided
        if not context_str:
            context_blocks = []
            for idx, c in enumerate(retrieved_chunks, 1):
                citation = c.get("citation", f"[Page {c['metadata'].get('page', '?')}]")
                context_blocks.append(f"--- CONTEXT BLOCK {idx} {citation} ---\n{c['text']}")
            context_str = "\n\n".join(context_blocks)

        # Extract unique citations for response metadata
        unique_sources = list(dict.fromkeys(
            c.get("citation", f"Page {c['metadata'].get('page', '?')}")
            for c in retrieved_chunks
        ))

        prompt = (
            f"STUDENT QUESTION:\n{query_text}\n\n"
            f"RETRIEVED NIE BIOLOGY TEXTBOOK CONTEXT:\n{context_str}\n\n"
            f"INSTRUCTION: Synthesize a structured, syllabus-compliant answer based strictly "
            f"on the NIE context above. Include citations matching the source blocks."
        )

        if not self.client:
            return {
                "answer": "⚠️ Error: GEMINI_API_KEY is missing from your .env configuration file.",
                "sources": [],
                "is_grounded": False,
                "chunks_used": len(retrieved_chunks)
            }

        # Call Gemini API with candidate model retry logic
        last_error = None
        for model in MODEL_CANDIDATES:
            try:
                if self.use_legacy:
                    model_obj = self.client.GenerativeModel(
                        model_name=model,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    response = model_obj.generate_content(
                        prompt,
                        generation_config={"temperature": self.temperature}
                    )
                    answer_text = response.text
                else:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=self.temperature
                        )
                    )
                    answer_text = response.text

                return {
                    "answer": answer_text,
                    "sources": unique_sources,
                    "is_grounded": True,
                    "chunks_used": len(retrieved_chunks),
                    "model_used": model
                }

            except Exception as e:
                last_error = e
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    print(f"⚠️ Quota exceeded for model {model}: {e}")
                    return {
                        "answer": (
                            "⌛ **Daily API Quota Limit Reached**\n\n"
                            "The free-tier API quota for Google Gemini has been exhausted for today "
                            "(1,000 requests/day limit on Free Tier).\n\n"
                            "**What you can do:**\n"
                            "- 🕒 Try again tomorrow when the daily API quota resets.\n"
                            "- 🔑 Or provide a new `GEMINI_API_KEY` in your `.env` or Streamlit Secrets configuration."
                        ),
                        "sources": unique_sources,
                        "is_grounded": False,
                        "chunks_used": len(retrieved_chunks),
                        "is_quota_error": True
                    }

                print(f"⚠️ Model {model} failed for generation: {e}. Trying fallback model...")
                time.sleep(1)

        err_str = str(last_error) if last_error else ""
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            return {
                "answer": (
                    "⌛ **Daily API Quota Limit Reached**\n\n"
                    "The free-tier API quota for Google Gemini has been exhausted for today "
                    "(1,000 requests/day limit on Free Tier).\n\n"
                    "**What you can do:**\n"
                    "- 🕒 Try again tomorrow when the daily API quota resets.\n"
                    "- 🔑 Or provide a new `GEMINI_API_KEY` in your `.env` or Streamlit Secrets configuration."
                ),
                "sources": unique_sources,
                "is_grounded": False,
                "chunks_used": len(retrieved_chunks),
                "is_quota_error": True
            }

        return {
            "answer": f"⚠️ Generation error: All Gemini model candidates failed. Last error: {last_error}",
            "sources": unique_sources,
            "is_grounded": False,
            "chunks_used": len(retrieved_chunks)
        }
