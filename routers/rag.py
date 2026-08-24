from fastapi import APIRouter, HTTPException
from models.schemas import QueryRequest, QueryResponse
from services.elastic_rag import ElasticRAGService
from services.loader import load_and_split_pdf
import os

router = APIRouter(prefix="/tag", tags=["RAG Operations"])

@router.post("/query", response_model=QueryResponse)
def quey_rag_endpoint(request: QueryRequest):
    """
        Endpoint to process RAG queries using user's Gemini API key (BYOK).
    """
    try:
        # Initialize the RAG service with the user's provided API key
        rag_service = ElasticRAGService(gemini_api_key=request.gemini_api_key)

        # Run the RAG query
        response = rag_service.query_rag(question=request.question)

        # Extract source documents page content, 
        source_docs = [doc.page_content for doc in response.get("source_documents", [])]

        return QueryResponse(
            answer=response.get("result", "No answer generated"),
            source_documents=source_docs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index-pdf")
def index_pdf_endpoint(gemini_api_key:str):
    """
        Endpoint to load and index the local PDF document into Elasticsearch.
    """
    try:
        pdf_path= os.path.join("data", "document.pdf")

        # Load and split the PDF
        chunks = load_and_split_pdf(pdf_path)

        #Initialize RAG service and index documents
        rag_service = ElasticRAGService(gemini_api_key= gemini_api_key)
        rag_service.index_documents(chunks)

        return {"status": "success", "message": f"Successfully indexed {len(chunks)} chunks into Elasticsearch."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))