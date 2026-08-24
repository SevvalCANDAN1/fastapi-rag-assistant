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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include RAG router
app.include_router(rag.router)

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