from flask import (
    Flask,
    render_template,
    request,
    jsonify,
)
from flask_cors import CORS
from src.helper import download_embeddings_model
from src.prompt import system_prompt
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# -----------------------------------------------------------------------------
# Flask app – serves React build + API
# -----------------------------------------------------------------------------
# Folder layout expected:
#   app.py
#   frontend/
#     dist/
#       index.html
#       assets/...
#
# Vite by default puts built JS/CSS in /assets.
# We map that to Flask's static folder.
app = Flask(
    __name__,
    static_folder="frontend/dist/assets",
    static_url_path="/assets",
    template_folder="frontend/dist",
)

# You don't strictly need CORS once React is served from the same origin,
# but keeping it doesn't hurt (useful during local dev).
CORS(app)

# -----------------------------------------------------------------------------
# ENV + KEYS
# -----------------------------------------------------------------------------
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY or ""
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY or ""

# -----------------------------------------------------------------------------
# Embeddings + Vector store + Retriever
# -----------------------------------------------------------------------------
# NOTE: change model_name or index_name if your project uses different ones.
embedding = download_embeddings_model(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
print("✅ Downloaded/loaded HuggingFace embeddings model.")

index_name = "legal-chatbot"  # <-- replace with your actual Pinecone index name

existing_vector_store = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embedding,
)
print(f"✅ Loaded existing Pinecone index: {index_name}")

retriever = existing_vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

# -----------------------------------------------------------------------------
# LLM + RAG chain
# -----------------------------------------------------------------------------
# You can swap model_name to your preferred one: "gpt-4.1", "gpt-4o", etc.
llm = ChatOpenAI(model_name="gpt-5-nano", temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt["content"]),  # includes {context}
        ("human", "User prompt:\n{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=prompt,
)

rag_chain = create_retrieval_chain(retriever, question_answer_chain)


# -----------------------------------------------------------------------------
# Helper to call the RAG chain
# -----------------------------------------------------------------------------
def generate_answer(user_input: str) -> str:
    """Run RAG chain and normalize answer field."""
    response = rag_chain.invoke({"input": user_input})

    answer = (
        response.get("answer")
        or response.get("Answer")
        or response.get("output_text")
        or str(response)
    )

    print(
        f"\n--- RAG CALL ---\n"
        f"User: {user_input}\n\n"
        f"Full response: {response}\n"
    )

    return answer


# -----------------------------------------------------------------------------
# SPA routes – Serve React (Vite) build
# -----------------------------------------------------------------------------
@app.route("/")
def serve_react_index():
    """
    Serve the Vite-built React app (frontend/dist/index.html).
    All static assets referenced in index.html (JS/CSS) are under /assets.
    """
    return render_template("index.html")


# Optional: catch-all for client-side routing (if you add React Router later)
@app.route("/<path:path>")
def spa_catch_all(path):
    # If the path starts with "api/", let API routes handle it (or 404).
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    # Otherwise, serve the SPA index (React will handle the route).
    return render_template("index.html")


# -----------------------------------------------------------------------------
# API endpoints
# -----------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    New API-style endpoint.

    Request JSON body:
      { "message": "your question here" }

    Response JSON:
      { "response": "answer text" }
    """
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or data.get("query") or "").strip()

    if not user_input:
        return jsonify(
            {"response": "Please type a question so I can help you."}
        )

    try:
        answer = generate_answer(user_input)
        return jsonify({"response": answer})
    except Exception as e:
        print("❌ ERROR in /api/chat:", e)
        return jsonify(
            {
                "response": (
                    "I am currently unable to generate an answer due to an internal error. "
                    "Please try again later or consult a qualified lawyer."
                )
            }
        )


# Backward-compatible legacy endpoint (GET /get?msg=...)
@app.route("/get", methods=["GET"])
def get_response():
    user_input = (request.args.get("msg") or "").strip()

    if not user_input:
        return jsonify(
            {"response": "Please type a question so I can help you."}
        )

    try:
        answer = generate_answer(user_input)
        return jsonify({"response": answer})
    except Exception as e:
        print("❌ ERROR in /get:", e)
        return jsonify(
            {
                "response": (
                    "I am currently unable to generate an answer due to an internal error. "
                    "Please try again later or consult a qualified lawyer."
                )
            }
        )


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # In production, you might run this with gunicorn/uwsgi instead.
    app.run(host="0.0.0.0", port=8080, debug=True)
