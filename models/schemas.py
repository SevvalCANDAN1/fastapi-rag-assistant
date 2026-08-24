from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """
        Schema for the incoming RAG query request, supporting BYOK (Bring Your Own Key).
    """
    question: str = Field(..., description="The user's question to the RAG system")

class QueryResponse(BaseModel):
    """
        Schema for the outgoing RAG query response.
    """
    answer: str = Field(..., description = "Generated answer from Gemini")
    source_documents: list[str] = Field(default=[], description="Retrieved chunks used as context")