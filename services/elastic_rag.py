import os
import base64
from elasticsearch import Elasticsearch
from langchain_community.vectorstores import ElasticsearchStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from fastapi import HTTPException
from core.config import settings
from functools import lru_cache

DEFAULT_SYSTEM_PROMPT = """You are a RAG assistant. Answer using ONLY the text inside <context>.
If the context is empty or does not contain the answer, say that this information is not in the uploaded documents. Do not invent facts.
If the question is in Turkish, answer in Turkish.
When you use a passage, mention the filename or page if that metadata appears in the context."""

SETTINGS_INDEX = "rag-workspace-settings"


def _build_authenticated_client(es_url: str, es_api_key: str) -> Elasticsearch:
    try:
        decoded = base64.b64decode(es_api_key).decode("utf-8")
        if ":" in decoded:
            api_id, api_secret = decoded.split(":", 1)
            return Elasticsearch(es_url, api_key=(api_id, api_secret))
    except Exception:
        pass
    return Elasticsearch(es_url, api_key=es_api_key)


@lru_cache(maxsize=1)
def get_es_client() -> Elasticsearch:
    """Single shared Elasticsearch client for the process (URL + API key from env)."""
    es_url = os.getenv("ELASTICSEARCH_URL") or settings.ELASTICSEARCH_URL
    es_api_key = (os.getenv("ELASTICSEARCH_API_KEY") or settings.ELASTICSEARCH_API_KEY or "").strip()
    if "localhost" not in es_url and not es_api_key:
        raise HTTPException(
            status_code=500,
            detail="Elasticsearch Cloud URL is configured, but ELASTICSEARCH_API_KEY is missing!",
        )
    if es_api_key:
        return _build_authenticated_client(es_url, es_api_key)
    return Elasticsearch(es_url)


class ElasticRAGService:
    def __init__(self, workspace_id: str, gemini_api_key: str | None = None):
        self.es_client = get_es_client()

        self.api_key = gemini_api_key
        self._embeddings = None

        safe = "".join(c for c in workspace_id.lower() if c.isalnum() or c in "-_")
        if not safe:
            raise HTTPException(status_code=400, detail="Invalid workspace_id")
        self.workspace_id = workspace_id
        self.workspace_safe = safe
        self.index_name = f"rag-{safe}"

    @property
    def embeddings(self):
        if not self.api_key:
            raise HTTPException(
                status_code=401,
                detail="Gemini API key required. Send header X-Gemini-Api-Key.",
            )
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=self.api_key,
            )
        return self._embeddings

    def get_system_prompt(self) -> tuple[str, bool]:
        try:
            res = self.es_client.get(index=SETTINGS_INDEX, id=self.workspace_safe)
            saved = (res["_source"] or {}).get("system_prompt") or ""
            if saved.strip():
                return saved.strip(), False
        except Exception:
            pass
        return DEFAULT_SYSTEM_PROMPT, True

    def set_system_prompt(self, prompt: str) -> tuple[str, bool]:
        text = (prompt or "").strip()
        if not text:
            try:
                self.es_client.delete(index=SETTINGS_INDEX, id=self.workspace_safe)
            except Exception:
                pass
            return DEFAULT_SYSTEM_PROMPT, True

        self.es_client.index(
            index=SETTINGS_INDEX,
            id=self.workspace_safe,
            document={
                "workspace_id": self.workspace_id,
                "system_prompt": text,
            },
        )
        return text, False

    def index_documents(self, chunks):
        """
        Indexes document chunks into Elasticsearch with vector embeddings.
        """
        store = ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.index_name,
            embedding=self.embeddings,
        )
        store.add_documents(chunks)
        return store

    def query_rag(self, question: str, system_prompt: str | None = None):
        """
        Queries the RAG pipeline using Elasticsearch retrieval and Gemini LLM via pure LCEL.
        """
        vector_store = ElasticsearchStore(
            es_connection=self.es_client,
            index_name=self.index_name,
            embedding=self.embeddings
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        def format_docs(docs):
            parts = []
            for doc in docs:
                meta = doc.metadata or {}
                label = meta.get("filename") or "document"
                page = meta.get("page")
                header = f"[{label}" + (f" p.{page}]" if page is not None else "]")
                parts.append(f"{header}\n{doc.page_content}")
            return "\n\n".join(parts)

        instructions = (system_prompt or "").strip()
        if not instructions:
            instructions, _ = self.get_system_prompt()

        prompt = ChatPromptTemplate.from_template("""
        {system_instructions}

        <context>
        {context}
        </context>
        
        Question: {question}
        """)
        
        retrieved_docs = retriever.invoke(question)
        context_text = format_docs(retrieved_docs)
        
        chain = (
            {
                "system_instructions": lambda _: instructions,
                "context": lambda _: context_text,
                "question": RunnablePassthrough(),
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        answer = chain.invoke(question)

        sources = []
        for doc in retrieved_docs:
            meta = doc.metadata or {}
            sources.append({
                "text": doc.page_content,
                "filename": meta.get("filename"),
                "page": meta.get("page"),
            })
        
        return {
            "result": answer,
            "source_documents": sources
        }

    