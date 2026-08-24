import os
from elasticsearch import Elasticsearch
from langchain_community.vectorstores import ElasticsearchStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from core.config import settings

class ElasticRAGService:
    """
        Manages Elasticsearch vector store indexing, retrieval, and Gemini LLM generation (BYOK).
    """
    def __init__(self, gemini_api_key:str):
        # Inıtıalize Elasticsearch client
        self.es_client = Elasticsearch(settings.ELASTICSEARCH_URL)
        self.api_key = gemini_api_key

        # Configure Gemini Embeddings using users api key
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key= self.api_key
        )
        self.index_name = "scikit-learn-rag-index"

    def index_documents(self, chunks):
        """
            Indexes document chunks into Elasticsearch with vector embeddings.
        """
        vector_store = ElasticsearchStore.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            es_url= settings.ELASTICSEARCH_URL,
            index_name= self.index_name,
            strategy= ElasticsearchStore.SparseRetrievalStrategy()
        )
        return vector_store

    def query_rag(self, question:str):
        """
            Queries the RAG pipeline using Elasticsearch retrieval and Gemini LLM.
        """
        vactor_store = ElasticsearchStore(
            es_url = settings.ELASTICSEARCH_URL,
            index_name = self.index_name,
            embedding = self.embeddings 
        )
        retriever = vector_store.as_retriever(search_kwargs={"k"=3})

        #Configure Gemini LLM for generation
        llm = ChatGoogleGenerativeAI(
            model= "gemini-2.5-pro",
            google_api_key = self.api_key,
            temperature = 0.3
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        response = qa_chain.invoke({"query": question})
        return response
