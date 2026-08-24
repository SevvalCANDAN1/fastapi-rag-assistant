from fastapi import APIRouter, Header, HTTPException
from models.schemas import QueryRequest, QueryResponse
from services.elastic_rag import ElasticRAGService
from services.loader import load_and_split_pdf
from core.config import settings
import os

router = APIRouter(tags=["RAG"])


def resolve_gemini_api_key(x_gemini_api_key: str | None) -> str:
    """Prefer the per-request BYOK header; fall back to optional server env."""
    api_key = (x_gemini_api_key or settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Gemini API key required. Send header X-Gemini-Api-Key.",
        )
    return api_key


@router.post("/query", response_model=QueryResponse)
def query_rag_endpoint(
    request: QueryRequest,
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
):
    """
        Process a RAG query. Gemini key is BYOK via header (not stored).
    """
    try:
        rag_service = ElasticRAGService(gemini_api_key=resolve_gemini_api_key(x_gemini_api_key))
        response = rag_service.query_rag(question=request.question)
        source_docs = [doc.page_content for doc in response.get("source_documents", [])]

        return QueryResponse(
            answer=response.get("result", "No answer generated"),
            source_documents=source_docs
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/index")
def index_pdf_endpoint(
    x_gemini_api_key: str | None = Header(default=None, alias="X-Gemini-Api-Key"),
):
    """
        Load and index the bundled PDF into Elasticsearch.
    """
    try:
        pdf_path = os.path.join("data", "document.pdf")
        chunks = load_and_split_pdf(pdf_path)
        rag_service = ElasticRAGService(gemini_api_key=resolve_gemini_api_key(x_gemini_api_key))
        rag_service.index_documents(chunks)

        return {"status": "success", "message": f"Successfully indexed {len(chunks)} chunks into Elasticsearch."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))