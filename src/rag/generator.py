"""
RAG Response Generator using Gemini API with strict NIE System Instructions.
"""
from google import genai
from typing import List, Dict, Any
from src.config import GEMINI_API_KEY, LLM_MODEL

SYSTEM_INSTRUCTION = """
You are A/L BioGenie, an expert AI tutor for Sri Lanka G.C.E. Advanced Level Biology (Unit 2: Chemical and Cellular Basis of Life).
Your task is to answer the student's question using ONLY the provided NIE Resource Book and Past Paper context snippets below.

Rules:
1. STRICT ADHERENCE: Use exact NIE Biology Resource Book definitions, keywords, and biological terms.
2. NO HALLUCINATION: Do NOT use international terms (e.g., AP/IB Biology) not present in the Sri Lankan A/L syllabus.
3. CITATION: Explicitly reference the source file and page numbers for your statements.
4. STRUCTURE: Format your answer clearly with:
   - Core Answer / Definition
   - Detailed Biological Explanation / Marking Scheme Criteria
   - NIE Resource Book Source Reference
"""

class RAGGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesize answer using Gemini API grounded in retrieved context chunks.
        """
        if not self.client:
            return "Error: GEMINI_API_KEY is not configured in .env file."

        context_str = "\n\n---\n\n".join([
            f"[Source: {c['metadata'].get('source', 'Unknown')}, Page {c['metadata'].get('page', '?')}]\n{c['text']}"
            for c in context_chunks
        ])

        prompt = f"""
STUDENT QUESTION: {query}

RETRIEVED CONTEXT SNIPPETS:
{context_str}

Please generate a structured, syllabus-compliant answer based ONLY on the context above.
"""

        response = self.client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )

        return response.text
