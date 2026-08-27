from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    """
        Incoming RAG query. Optional system_prompt overrides the workspace prompt for this request only.
    """
    question: str = Field(..., description="The user's question to the RAG system")
    system_prompt: str | None = Field(
        default=None,
        description="Optional one-shot override; omit to use the saved workspace prompt or the default.",
    )


class SourceChunk(BaseModel):
    text: str
    filename: str | None = None
    page: int | None = None


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer from Gemini")
    source_documents: list[SourceChunk] = Field(
        default_factory=list,
        description="Retrieved chunks with source metadata",
    )


class SystemPromptBody(BaseModel):
    system_prompt: str = Field(
        ...,
        description="Custom instructions for this workspace. Empty string resets to the default.",
    )


class SystemPromptResponse(BaseModel):
    system_prompt: str
    is_default: bool

class LLMModelOption(BaseModel):
    provider: str = Field(
        ...,
        description="LLM provider identifier.",
    )
    model: str = Field(
        ...,
        description="Model identifier sent to the provider API.",
    )
    display_name: str = Field(
        ...,
        description="Human-readable model name.",
    )


class LLMModelsResponse(BaseModel):
    models: list[LLMModelOption]


class EmbeddingModelOption(BaseModel):
    provider: str = Field(
        ...,
        description="Embedding provider identifier.",
    )
    model: str = Field(
        ...,
        description="Embedding model identifier sent to the provider API.",
    )
    display_name: str = Field(
        ...,
        description="Human-readable embedding model name.",
    )


class EmbeddingModelsResponse(BaseModel):
    llm_provider: str
    llm_model: str
    models: list[EmbeddingModelOption]