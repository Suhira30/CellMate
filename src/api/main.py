"""
FastAPI Backend Application for CellMate RAG System.
Provides production REST endpoints for question answering, health checks, and vector DB stats.
"""
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import TOP_K, LLM_MODEL, EMBEDDING_MODEL
from src.rag.pipeline import CellMateRAG


# ─── Pydantic Request & Response Schemas ───────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="The student's A/L Biology question",
        example="What are the unique properties of water that make it essential for life?"
    )
    top_k: Optional[int] = Field(
        default=TOP_K,
        ge=1,
        le=10,
        description="Number of context passages to retrieve"
    )
    doc_type_filter: Optional[str] = Field(
        default=None,
        description="Filter by document type: 'resource_book', 'past_paper', 'model_paper'"
    )


class CitationSchema(BaseModel):
    source_file: str
    page_number: Any
    section_heading: str
    doc_type: str
    markdown_badge: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationSchema]
    is_grounded: bool
    chunks_used: int
    model_used: str
    latency_seconds: float


class HealthResponse(BaseModel):
    status: str
    unit: str
    vector_db_connected: bool
    total_chunks_indexed: int
    embedding_model: str
    llm_model: str


class SystemStatsResponse(BaseModel):
    collection_name: str
    total_chunks: int
    vectorstore_path: str
    embedding_model: str
    similarity_metric: str


# ─── FastAPI App Initialization ────────────────────────────────────────────────

app = FastAPI(
    title="CellMate RAG API",
    description="Sri Lanka G.C.E. Advanced Level Biology (Unit 02) RAG Backend API powered by Google Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for Streamlit UI and local web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG Pipeline Singleton
rag_pipeline: Optional[CellMateRAG] = None


@app.on_event("startup")
def startup_event():
    """Initializes RAG Pipeline singleton on backend app startup."""
    global rag_pipeline
    print("🚀 Initializing CellMate RAG Pipeline...")
    try:
        rag_pipeline = CellMateRAG()
        print("✅ CellMate RAG Pipeline initialized successfully.")
    except Exception as e:
        print(f"⚠️ Error initializing CellMate RAG Pipeline: {e}")


# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/", tags=["General"])
def read_root():
    """Root welcome endpoint providing API metadata."""
    return {
        "app": "CellMate RAG API",
        "description": "G.C.E. A/L Biology (Unit 02) AI Tutor",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Returns backend API and ChromaDB vector store health status."""
    global rag_pipeline
    vector_connected = False
    total_chunks = 0

    if rag_pipeline and rag_pipeline.retriever and rag_pipeline.retriever.store_manager:
        try:
            stats = rag_pipeline.retriever.store_manager.get_stats()
            total_chunks = stats.get("total_chunks", 0)
            vector_connected = True
        except Exception:
            vector_connected = False

    return HealthResponse(
        status="healthy",
        unit="Unit 02 - Chemical & Cellular Basis of Life",
        vector_db_connected=vector_connected,
        total_chunks_indexed=total_chunks,
        embedding_model=EMBEDDING_MODEL,
        llm_model=LLM_MODEL
    )


@app.get("/api/v1/system/stats", response_model=SystemStatsResponse, tags=["System"])
def get_system_stats():
    """Returns vector store indexed document and chunk statistics."""
    global rag_pipeline
    if not rag_pipeline or not rag_pipeline.retriever:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG Pipeline is not initialized."
        )

    stats = rag_pipeline.retriever.store_manager.get_stats()
    return SystemStatsResponse(
        collection_name=stats.get("collection_name", "nie_biology_unit02"),
        total_chunks=stats.get("total_chunks", 0),
        vectorstore_path=stats.get("vectorstore_path", ""),
        embedding_model=stats.get("embedding_model", EMBEDDING_MODEL),
        similarity_metric=stats.get("similarity_metric", "cosine")
    )


@app.post("/api/v1/query", response_model=QueryResponse, tags=["RAG Question Answering"])
def process_query(request: QueryRequest):
    """
    Processes a student's A/L Biology question through the full RAG pipeline:
    Extracts question -> Vector Search -> Cosine Thresholding -> Gemini LLM Grounded Answer.
    """
    global rag_pipeline
    if not rag_pipeline:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG Pipeline is not initialized."
        )

    start_time = time.time()

    try:
        result = rag_pipeline.answer_question(
            query=request.query,
            top_k=request.top_k,
            doc_type_filter=request.doc_type_filter,
            include_citation_footer=True
        )

        latency = round(time.time() - start_time, 3)

        citations_schema = [
            CitationSchema(
                source_file=c.get("source_file", ""),
                page_number=c.get("page_number", "?"),
                section_heading=c.get("section_heading", ""),
                doc_type=c.get("doc_type", ""),
                markdown_badge=c.get("markdown_badge", "")
            )
            for c in result.get("citations", [])
        ]

        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            citations=citations_schema,
            is_grounded=result["is_grounded"],
            chunks_used=len(result.get("retrieved_chunks", [])),
            model_used=result.get("model_used", LLM_MODEL),
            latency_seconds=latency
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your query: {str(e)}"
        )
