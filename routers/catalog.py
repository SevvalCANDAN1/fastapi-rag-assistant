from fastapi import APIRouter, HTTPException, Query
from core.model_catalog import (
    LLM_MODELS,
    LLM_MODEL_IDS,
    LLM_PROVIDERS,
    recommended_embeddings_for,
)
from models.schemas import (
    EmbeddingModelOption,
    EmbeddingModelsResponse,
    LLMModelOption,
    LLMModelsResponse,
)

router = APIRouter(
    prefix="/catalog",
    tags=["Model Catalog"],
)

@router.get(
    "/llm-models",
    response_model=LLMModelsResponse,
)
def get_llm_models() -> LLMModelsResponse:
    models = [
        LLMModelOption(
            provider=item.provider,
            model=item.model,
            display_name=item.display_name,
        )
        for item in LLM_MODELS
    ]
    return LLMModelsResponse(models=models)

@router.get(
    "/embedding-models",
    response_model=EmbeddingModelsResponse,
)
def get_embedding_models(
    llm_provider: str = Query(..., enum=LLM_PROVIDERS),
    llm_model: str = Query(..., enum=LLM_MODEL_IDS),
) -> EmbeddingModelsResponse:
    recommendations = recommended_embeddings_for(
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Unknown LLM model: "
                f"{llm_provider}/{llm_model}"
            ),
        )
    models = [
        EmbeddingModelOption(
            provider=item.provider,
            model=item.model,
            display_name=item.display_name,
        )
        for item in recommendations
    ]
    return EmbeddingModelsResponse(
        llm_provider=llm_provider.strip().lower(),
        llm_model=llm_model.strip(),
        models=models,
    )