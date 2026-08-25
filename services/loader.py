import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_split_pdf(
        file_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        extra_metadata: dict | None = None):
    """
        Loads a PDF document and splits it into manageable text chunks for RAG.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    loader = PyPDFLoader(file_path)
    pages = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = text_splitter.split_documents(pages)
    extra = extra_metadata or {}
    for chunk in chunks:
        chunk.metadata.update(extra)
    return chunks