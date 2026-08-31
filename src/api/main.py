"""
FastAPI Backend Application for A/L BioGenie RAG System.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(
    title="A/L BioGenie RAG API",
    description="RAG API for G.C.E. A/L Biology (Unit 2 MVP) in Sri Lanka using Gemini API.",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {"message": "Welcome to A/L BioGenie RAG API", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "unit": "Unit 2 - Chemical & Cellular Basis of Life"}

@app.post("/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    """
    Process student query through RAG pipeline.
    """
    # Placeholder response until vector DB is populated
    return QueryResponse(
        query=request.query,
        answer="Please ingest Unit 2 PDF files and set your GEMINI_API_KEY in .env to receive grounded RAG responses.",
        sources=[]
    )
