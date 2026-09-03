from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

def get_chat_model(provider: str, model: str, api_key:str) -> object:
    """Build a Langchain chat model for the given provider"""
    p = provider.strip().lower()
    if p == "google":
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature= 0.3,
        )
    if p == "openai":
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.3,
        )
    if p == "anthropic":
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.3,
        )
    if p == "groq":
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=0.3,
        )
    raise HTTPException(400, f"Unsupported LLM provider: {provider}")