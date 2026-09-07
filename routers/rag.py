from fastapi import APIRouter, Header, HTTPException, UploadFile, File
from models.schemas import QueryRequest, QueryResponse, SystemPromptBody, SystemPromptResponse, WorkspaceModelsBody, WorkspaceModelsResponse
from services.elastic_rag import ElasticRAGService
from services.loader import load_and_split_pdf
from core.config import settings
import tempfile
import os

router = APIRouter(tags=["RAG"])


def resolve_llm_api_key(x_llm_api_key: str | None) -> str | None:
    """BYOK LLM key via header. Returns None if not provided (service may fall back to env)."""
    return (x_llm_api_key or "").strip() or None

def resolve_embedding_api_key(x_embedding_api_key: str | None) -> str | None:
    """BYOK embedding key via header. Returns None if not provided."""
    return (x_embedding_api_key or "").strip() or None

def resolve_workspace_id(x_workspace_id: str | None) -> str:
    ws = (x_workspace_id or "").strip()
    if not ws:
        raise HTTPException(401, "X-Workspace-Id header required.")
    return ws


@router.post("/query", response_model=QueryResponse)
def query_rag_endpoint(
    request: QueryRequest,
    x_llm_api_key: str | None = Header(default=None, alias="X-Llm-Api-Key"),
    x_embedding_api_key: str | None = Header(default=None, alias="X-Embedding-Api-Key"),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    """
        Process a RAG query. Gemini key is BYOK via header (not stored).
    """
    try:
        rag_service = ElasticRAGService(
            workspace_id=resolve_workspace_id(x_workspace_id),
            llm_api_key=resolve_llm_api_key(x_llm_api_key),
            embedding_api_key=resolve_embedding_api_key(x_embedding_api_key),
        )
        response = rag_service.query_rag(
            question=request.question,
            system_prompt=request.system_prompt,
        )

        return QueryResponse(
            answer=response.get("result", "No answer generated"),
            source_documents=response.get("source_documents", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")


@router.post("/documents/index")
async def index_pdf_endpoint(
    file: UploadFile = File(...),
    x_llm_api_key: str | None = Header(default=None, alias="X-Llm-Api-Key"),
    x_embedding_api_key: str | None = Header(default=None, alias="X-Embedding-Api-Key"),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    """
        Load and index the bundled PDF into Elasticsearch.
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Only PDF files are allowed.")

    data = await file.read()
    if len(data) > 10*1024*1024:
        raise HTTPException(400, "Max file size is 10MB.")

    workspace_id = resolve_workspace_id(x_workspace_id)
    llm_key = resolve_llm_api_key(x_llm_api_key)
    embedding_key = resolve_embedding_api_key(x_embedding_api_key)

    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        chunks = load_and_split_pdf(
            tmp_path,
            extra_metadata={
                 "workspace_id": workspace_id,
                "filename": file.filename,
            },
        )
        rag_service = ElasticRAGService(
            workspace_id=workspace_id,
            llm_api_key=llm_key,
            embedding_api_key=embedding_key,
        )
        rag_service.index_documents(chunks)
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "filename": file.filename,
            "chunks": len(chunks),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, "Indexing failed")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/prompt", response_model=SystemPromptResponse)
def get_prompt_endpoint(
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    rag_service = ElasticRAGService(workspace_id=resolve_workspace_id(x_workspace_id))
    prompt, is_default = rag_service.get_system_prompt()
    return SystemPromptResponse(system_prompt=prompt, is_default=is_default)


@router.put("/prompt", response_model=SystemPromptResponse)
def put_prompt_endpoint(
    body: SystemPromptBody,
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    rag_service = ElasticRAGService(workspace_id=resolve_workspace_id(x_workspace_id))
    prompt, is_default = rag_service.set_system_prompt(body.system_prompt)
    return SystemPromptResponse(system_prompt=prompt, is_default=is_default)

@router.get("/workspace/models", response_model=WorkspaceModelsResponse)
def get_models_endpoint(
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    rag_service = ElasticRAGService(workspace_id=resolve_workspace_id(x_workspace_id))
    return rag_service.get_models()

@router.put("/workspace/models", response_model=WorkspaceModelsResponse)
def put_models_endpoint(
    body: WorkspaceModelsBody,
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
):
    rag_service = ElasticRAGService(workspace_id=resolve_workspace_id(x_workspace_id))
    return rag_service.set_models(body)