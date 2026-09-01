from fastapi import HTTPException
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_voyageai import VoyageAIEmbeddings

def get_embeddings(provider: str, model: str, api_key:str) -> object:
    """Build a Langchain embeddings client for the given provider"""
    p = provider.strip().lower()
    if p == "google":
        return GoogleGenerativeAIEmbeddings(
            model=f"models/{model}",
            google_api_key=api_key,
        )
    if p == "openai":
        return OpenAIEmbeddings(
            model=model,
            api_key=api_key,
        )
    if p == "voyage":
        return VoyageAIEmbeddings(
            model=model,
            voyage_api_key=api_key,
        )
    raise HTTPException(400, f"Unsupported embedding provider: {provider}")