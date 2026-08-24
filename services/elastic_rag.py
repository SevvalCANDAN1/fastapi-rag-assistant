import os
from elasticsearch import Elasticsearch
from langchain_community.vectorstores import ElasticsearchStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from fastapi import HTTPException
from core.config import settings

class ElasticRAGService:
    """
    Manages Elasticsearch vector store indexing, retrieval, and Gemini LLM generation (BYOK) using pure LCEL.
    """
    def __init__(self, gemini_api_key: str):
        # Ayarlardan veya doğrudan çevresel değişkenlerden URL ve API Key'i alıyoruz
        class ElasticRAGService:
    """
    Manages Elasticsearch vector store indexing, retrieval, and Gemini LLM generation (BYOK) using pure LCEL.
    """
    def __init__(self, gemini_api_key: str):
        # Ayarlardan veya doğrudan çevresel değişkenlerden URL ve API Key'i alıyoruz
        es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY", None)

        if "localhost" not in es_url and not es_api_key:
            raise HTTPException(
                status_code=500, 
                detail="Elasticsearch Cloud URL is configured, but ELASTICSEARCH_API_KEY is missing!"
            )

        if es_api_key:
            # Curl ile başarılı olduğumuz yöntemi (Authorization headers) uyguluyoruz
            self.es_client = Elasticsearch(
                es_url,
                headers={"Authorization": f"ApiKey {es_api_key}"}
            )
        else:
            self.es_client = Elasticsearch(es_url)
        
        self.api_key = gemini_api_key
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.api_key
        )
        
        self.index_name = "scikit-learn-rag-index"

    def index_documents(self, chunks):
        """
        Indexes document chunks into Elasticsearch with vector embeddings.
        """
        vector_store = ElasticsearchStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            es_url=settings.ELASTICSEARCH_URL,
            index_name=self.index_name,
            #strategy=ElasticsearchStore.SparseRetrievalStrategy()
        )
        return vector_store

    def query_rag(self, question: str):
        """
        Queries the RAG pipeline using Elasticsearch retrieval and Gemini LLM via pure LCEL.
        """
        vector_store = ElasticsearchStore(
            es_url=settings.ELASTICSEARCH_URL,
            index_name=self.index_name,
            embedding=self.embeddings
        )
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Configure Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )
        
        # Format retrieved documents into a single text string
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Modern LCEL chain construction (bypasses any langchain.chains issues)
        prompt = ChatPromptTemplate.from_template("""
        You are an expert AI assistant. Answer the user's question accurately using the provided context. 
        If the question is in Turkish, you can translate and synthesize the answer from the English context into fluent Turkish.
        If the context does not have the exact answer, use your knowledge to provide a helpful response.

        <context>
        {context}
        </context>
        
        Question: {question}
        """)
        
        retrieved_docs = retriever.invoke(question)
        context_text = format_docs(retrieved_docs)
        
        # Construct the chain manually and cleanly
        chain = (
            {"context": lambda x: context_text, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        answer = chain.invoke(question)
        
        return {
            "result": answer,
            "source_documents": retrieved_docs
        }