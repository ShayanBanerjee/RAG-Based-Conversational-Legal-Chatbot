from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceBgeEmbeddings
from typing import List
from langchain.schema import Document

# Extract data from PDF
def load_pdf_files(data):
    loader = DirectoryLoader(
        data,
        glob="*.pdf",
        loader_cls=PyPDFLoader
    )
    documents = loader.load()
    return documents

def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    """Given a list of document object, return a new list of document objects
    containing only 'source' in metadata and the original page content
    """
    minimal_docs : List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src}
            )
        )
    return minimal_docs

def text_split_documents(documents: List[Document], chunk_size: int = 500, chunk_overlap: int = 20) -> List[Document]:
    """Split documents into smaller chunks using RecursiveCharacterTextSplitter."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs

def download_embeddings_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> HuggingFaceBgeEmbeddings:
    """Download and return the HuggingFace BGE embeddings model."""
    embeddings = HuggingFaceBgeEmbeddings(
        model_name=model_name      
    )
    return embeddings 