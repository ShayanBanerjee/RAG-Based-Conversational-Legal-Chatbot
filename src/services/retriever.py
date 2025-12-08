from dotenv import load_dotenv
import os

from src.helper import download_embeddings_model
from langchain_pinecone import PineconeVectorStore

# Load env variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Make sure the SDK sees them
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Same model + index as app.py
embedding = download_embeddings_model(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

INDEX_NAME = "legal-chatbot"  # keep in sync with app.py

# Single global VectorStore + retriever
_vector_store = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embedding,
)

_retriever = _vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)


def retrieve_context(query: str) -> list[str]:
    """
    Retrieve relevant context passages for a given query from Pinecone.

    Returns a list of plain text chunks (page_content).
    """
    docs = _retriever.get_relevant_documents(query)
    return [d.page_content for d in docs]
