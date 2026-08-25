from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import rag

# Initialize FastAPI application
app = FastAPI(
    title= settings.PROJECT_NAME,
    version="1.0.0",
    description="Production-ready RAG Assistant with FastAPI, Elasticsearch, and Gemini BYOK / FastAPI"
)

# Browser only allows JS calls from origins listed here (from ALLOWED_ORIGINS env).
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Gemini-Api-Key", "X-Workspace-Id"],
)

app.include_router(rag.router, prefix="/rag/v1")

@app.get("/rag/v1/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    """
        Root endpoint to check if the API is running.
    """
    return{
        "status": "online",
        "project": settings.PROJECT_NAME,
        "message": "Welcome to the Production RAG Assistant API! / Production RAG Asistanı API'sine hoş geldiniz!",
    }