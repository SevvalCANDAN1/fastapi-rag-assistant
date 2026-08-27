from dataclasses import dataclass

@dataclass(frozen=True)
class ModelRef:
    provider: str
    model: str

@dataclass(frozen=True)
class EmbeddingModel:
    provider: str
    model: str
    display_name: str

    @property
    def ref(self) -> ModelRef:
        return ModelRef(
            provider=self.provider,
            model=self.model,
        )

@dataclass(frozen=True)
class LLMModel:
    provider: str
    model: str
    display_name: str
    recommended_embeddings: tuple[ModelRef, ...]

EMBEDDING_MODELS: tuple[EmbeddingModel, ...] = (
    EmbeddingModel(
        provider="google",
        model="gemini-embedding-001",
        display_name="Gemini Embedding 001",
    ),
    EmbeddingModel(
        provider="openai",
        model="text-embedding-3-small",
        display_name="OpenAI Text Embedding 3 Small",
    ),
    EmbeddingModel(
        provider="voyage",
        model="voyage-4-lite",
        display_name="Voyage 4 Lite",
    ),
)

LLM_MODELS: tuple[LLMModel, ...] = (
    LLMModel(
        provider="google",
        model="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        recommended_embeddings=(
            ModelRef(
                provider="google",
                model="gemini-embedding-001",
            ),
        ),
    ),
    LLMModel(
        provider="openai",
        model="gpt-4o-mini",
        display_name="GPT-4o Mini",
        recommended_embeddings=(
            ModelRef(
                provider="openai",
                model="text-embedding-3-small",
            ),
        ),
    ),
    LLMModel(
        provider="anthropic",
        model="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        recommended_embeddings=(
            ModelRef(
                provider="voyage",
                model="voyage-4-lite",
            ),
            ModelRef(
                provider="openai",
                model="text-embedding-3-small",
            ),
        ),
    ),
    LLMModel(
        provider="groq",
        model="openai/gpt-oss-120b",
        display_name="GPT-OSS 120B via Groq",
        recommended_embeddings=(
            ModelRef(
                provider="voyage",
                model="voyage-4-lite",
            ),
            ModelRef(
                provider="openai",
                model="text-embedding-3-small",
            ),
        ),
    ),
)

def find_llm_model(
        provider: str,
        model: str,
) -> LLMModel | None:
    provider = provider.strip().lower()
    model.strip()

    return next(
        (
            item
            for item in LLM_MODELS
            if item.provider == provider and item.model == model
        ),
        None,
    )

def find_embedding_model(
        provider: str,
        model: str,
) -> EmbeddingModel | None:
    provider = provider.strip().lower()
    model = model.strip()

    return next(
        (
            item
            for item in EMBEDDING_MODELS
            if item.provider == provider and item.model == model
        ),
        None,
    )


def recommended_embeddings_for(
    llm_provider: str,
    llm_model: str,
) -> tuple[EmbeddingModel, ...] | None:
    llm = find_llm_model(llm_provider, llm_model)
    if llm is None:
        return None
    recommendations: list[EmbeddingModel] = []
    for reference in llm.recommended_embeddings:
        embedding = find_embedding_model(
            provider=reference.provider,
            model=reference.model,
        )
        if embedding is None:
            raise RuntimeError(
                "Model catalog contains an unknown embedding reference: "
                f"{reference.provider}/{reference.model}"
            )
        recommendations.append(embedding)
    return tuple(recommendations)