from dotenv import load_dotenv
import os
from src.helper import load_pdf_files, filter_to_minimal_docs, text_split_documents, download_embeddings_model
from pinecone import Pinecone
from pinecone import ServerlessSpec

load_dotenv()  

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  

extracted = load_pdf_files(data="data")
print(f"✅ Loaded {len(extracted)} documents from PDF files.")  
filtered_docs = filter_to_minimal_docs(extracted)
print(f"✅ Filtered documents to minimal metadata.")    
text_chunk = text_split_documents(filtered_docs, chunk_size=500, chunk_overlap=20)
print(f"✅ Split documents into {len(text_chunk)} text chunks.")
embedding = download_embeddings_model(model_name="sentence-transformers/all-MiniLM-L6-v2")  
print("✅ Downloaded HuggingFace BGE embeddings model.")
# 4. Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index if it doesn't exist
index_name = "legal-chatbot"

if not pc.has_index(index_name):
    pc.create_index(
        name = index_name,
        dimension=384,  # Dimension of the embeddings
        metric= "cosine",  # Cosine similarity
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    
# Connect to the index
index = pc.Index(index_name)

# 5. Create Pinecone VectorStore from documents
from langchain_pinecone import PineconeVectorStore

try:
    docsearch = PineconeVectorStore.from_documents(
        documents=text_chunk,
        embedding=embedding,
        index_name=index_name
    )
    print("✅ Pinecone VectorStore created successfully.")
except Exception as e:
    print(f"❌ Error creating Pinecone VectorStore: {e}")