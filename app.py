from flask import Flask, render_template, request, jsonify
from src.helper import download_embeddings_model
from src.prompt import system_prompt
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

app = Flask(__name__)

# -------------------- ENV + MODELS --------------------
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY or ""
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY or ""

# Embeddings model
embedding = download_embeddings_model(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
print("✅ Downloaded HuggingFace embeddings model.")

# -------------------- VECTOR STORE + RETRIEVER --------------------
index_name = "legal-chatbot"

existing_vector_store = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embedding,
)
print("✅ Existing Pinecone VectorStore loaded successfully.")

retriever = existing_vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3},
)

# -------------------- LLM + RAG CHAIN --------------------
# Use your chosen cheap model
llm = ChatOpenAI(model_name="gpt-5-nano", temperature=0)

# system_prompt["content"] already contains {context}
# We add a human message with {input}
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt["content"]),
        ("human", "User prompt:\n{input}")
    ]
)
# Now the prompt has input variables: ["context", "input"]

question_answer_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=prompt,
)

rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# -------------------- ROUTES --------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get", methods=["GET"])
def get_response():
    user_input = (request.args.get("msg") or "").strip()

    if not user_input:
        return jsonify({"response": "Please type a question so I can help you."})

    try:
        # create_retrieval_chain expects "input"
        response = rag_chain.invoke({"input": user_input})

        # Inspect common keys
        answer = (
            response.get("answer")
            or response.get("Answer")
            or response.get("output_text")
            or str(response)
        )

        print(f"\n--- RAG CALL ---\nUser: {user_input}\n\nFull response: {response}\n")
        return jsonify({"response": answer})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({
            "response": (
                "I am currently unable to generate an answer due to an internal error. "
                "Please try again later or consult a qualified lawyer."
            )
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
