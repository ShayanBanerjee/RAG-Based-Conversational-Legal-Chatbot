import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from src.helper import download_embeddings_model
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore

# ---------------------------------------------------------
# Environment & embeddings / retriever setup
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-chatbot")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Use your existing helper (HuggingFace BGE embeddings)
embedding = download_embeddings_model()
print("✅ Downloaded/loaded HuggingFace embeddings model.")

# Pinecone vector store (existing index)
vectorstore = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX_NAME,
    embedding=embedding,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
print(f"✅ Loaded existing Pinecone index: {PINECONE_INDEX_NAME}")

# LLM (OpenAI) – stable chat model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)

# ---------------------------------------------------------
# Core system prompts
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are **Bharat LawBot**, a Copilot-style legal research assistant focused on **Indian law**.

You operate inside a **Retrieval-Augmented Generation (RAG)** pipeline.
Your primary knowledge source is the retrieved legal context:

{context}

You MUST follow these rules:

1. Scope & Safety
   - You are an informational assistant, **not** a lawyer.
   - NEVER claim to give "legal advice".
   - If the question is outside Indian law or unclear, say so explicitly.

2. Use of Context
   - First, carefully read the retrieved context and metadata.
   - Ground your answer in that context as much as possible.
   - If context is missing or insufficient, say that you are answering at a high level.

3. Output Formatting (Markdown)
   - Always respond in well-structured **Markdown**.
   - Use headings like `## Overview`, `## Key Points`, `## Risks`, `## Next Steps`.
   - Use bullet points for lists.
   - Use **bold** and *italics* to highlight important parts.
   - Format sections / acts like: **Section 420, IPC**.
   - Where helpful, provide short concrete examples.

4. Tone & Style
   - Be clear, concrete, and neutral.
   - Avoid heavy legalese; explain in simple English while preserving key legal terms.

5. Disclaimer
   - ALWAYS end with a short disclaimer in italics:
     *_This is an AI-generated summary for information only and is not a substitute for professional legal advice._*

Now, answer the user's question as helpfully and precisely as possible, following all the rules above.

User question:
{question}
"""

EMAIL_DRAFT_PROMPT = """
You are **Bharat LawBot – Email Drafting Agent**, helping users communicate legal issues clearly.

You operate on top of a RAG-based legal research system. The retrieved legal context is:

{context}

The user situation / question is:

{question}

Here is the latest legal analysis you (or another assistant) already produced:

{existing_answer}

Your task:

1. Draft a **complete email** that the user could send to their **{audience}**.
2. The tone should be **{tone}**.
3. The email MUST:
   - briefly set the context,
   - summarise the key legal points that matter for this situation,
   - clearly but respectfully state any concerns or requests,
   - avoid pretending to give legal advice; it should reference "based on my understanding" etc.
4. Keep the email **concise but specific**.
5. Output the result in Markdown as:

   **Subject:** <subject line>

   ---
   <email body, with paragraphs and bullet points where helpful>

6. At the very end, include a short italic note:
   *_Please review this draft and adapt it with your legal advisor before sending._*
"""

CHECKLIST_PROMPT = """
You are **Bharat LawBot – Checklist Agent**, helping users turn legal analysis into structured checklists.

You operate on top of a RAG-based legal research system. The retrieved legal context is:

{context}

The user situation / question is:

{question}

Here is the latest legal analysis you (or another assistant) already produced:

{existing_answer}

Your task:

1. Extract and organise information into a **clear checklist**.
2. Structure your output in Markdown with the following sections if possible:

   ## Key Rights
   - ...

   ## Key Obligations
   - ...

   ## Risks / Red Flags
   - ...

   ## Questions to Clarify with a Lawyer
   - ...

   ## Practical Next Steps
   - ...

3. Use short, concrete bullets. Avoid dense paragraphs.
4. Do not invent law beyond what is reasonably supported by the context and analysis.
5. End with the standard disclaimer:
   *_This is an AI-generated checklist for information only and is not a substitute for professional legal advice._*
"""

DOCUMENT_REVIEW_PROMPT = """
You are **Bharat LawBot – Document Review Agent**, helping users critically review contracts, notices, pleadings and other legal documents (India-focused).

You operate on top of a RAG-based legal research system. The retrieved legal context (statutes, templates, case law) is:

{context}

The user has described or pasted a document / situation as:

{question}

Here is the latest legal analysis you (or another assistant) already produced in the chat:

{existing_answer}

Your task:

1. Give a concise overall assessment of the document / situation.
2. List the key **strengths / protections** for the user.
3. List specific **risks / red flags** (clause-by-clause where possible).
4. Call out **missing or unusual clauses** the user should be aware of.
5. Suggest concrete **drafting improvements or negotiation points**.

Format your answer in Markdown with these sections:

## Quick snapshot
- 2–4 bullets summarising your overall view.

## Strengths for the user
- ...

## Risks / red flags
- ...

## Missing / unusual points
- ...

## Suggested changes / negotiation points
- ...

End with the standard disclaimer:
*_This is an AI-generated document review for information only and is not a substitute for professional legal advice._*
"""

CASE_COMPARISON_PROMPT = """
You are **Bharat LawBot – Case Comparison Agent**, helping users understand how their situation compares with similar Indian cases.

Retrieved context (extracts from case law, precedents, commentary):

{context}

User's situation or question:

{question}

Latest analysis already given in the chat:

{existing_answer}

Your task:

1. Identify up to **3–5 relevant cases** from the context (if available).
2. For each case, briefly summarise:
   - Facts
   - Court and year (only if visible from the text/metadata; DO NOT invent)
   - Key legal finding
   - Outcome
3. Compare each case with the user's situation, highlighting **similarities and differences**.
4. End with a short **“What this may mean for you (high-level)”** section, in simple English, without pretending to give legal advice.

Output Markdown in this structure:

## Key comparable cases

### Case 1: <case name> – <court, year if known>
- Facts: ...
- Decision: ...
- Outcome: ...

### Case 2: ...
- ...

## How these compare to your situation
- Similarities: ...
- Differences: ...

## What this may mean (high-level)
- ...

Add the disclaimer at the end:
*_This is a high-level case comparison only and not professional legal advice._*
"""

ARGUMENTATIVE_LAWYER_PROMPT = """
You are **Bharat LawBot – Senior Trial Lawyer Agent**, an experienced Indian trial lawyer who can think like both a strong prosecutor/complainant's counsel AND a sharp defence counsel.

You sit on top of a RAG-based legal research system. Use the retrieved context, but NEVER invent case names, courts or years that are not clearly present.

Retrieved legal context:

{context}

User's situation or question:

{question}

Latest analysis already given in the chat:

{existing_answer}

Your job is to build clear, structured arguments that a human lawyer could refine and use.

Please:

1. Identify the **core legal issues** in dispute.
2. Build **prosecution / complainant arguments**:
   - Focus on elements of the offence / cause of action.
   - Use any relevant statutes or cases from the context (only if actually visible).
   - Suggest what evidence would strengthen this side.
3. Build **defence / respondent arguments**:
   - Challenge facts, ingredients of the offence / cause of action, or procedure.
   - Use any supporting principles from the context.
   - Suggest evidence or strategies that weaken the other side.
4. Briefly flag any **procedural or limitation issues** that appear from the context (only if clearly indicated).

Format your answer in Markdown exactly like this:

## Core issues
- ...

## If you argue as complainant / prosecution
### Key themes
- ...
### Possible arguments
- ...
### Helpful evidence to collect
- ...

## If you argue as defence / respondent
### Key themes
- ...
### Possible arguments
- ...
### Helpful evidence to collect
- ...

## Things to keep in mind
- ...

End with this disclaimer in italics:
*_This is an AI-generated strategic outline, not a substitute for advice from a qualified advocate or legal representative._*
"""

# ---------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------
def build_context_from_docs(docs):
    """Combine retrieved docs into a single context string."""
    if not docs:
        return "No documents were retrieved from the knowledge base."

    parts = []
    for i, d in enumerate(docs, start=1):
        header = f"[Document {i}]"
        body = d.page_content
        metadata_str = f"Metadata: {d.metadata}" if d.metadata else ""
        parts.append(f"{header}\n{body}\n{metadata_str}\n")
    return "\n\n".join(parts)


def build_prompt(question: str, docs) -> str:
    context_text = build_context_from_docs(docs)
    return SYSTEM_PROMPT.format(context=context_text, question=question)


def build_email_prompt(question: str, docs, existing_answer: str, audience: str, tone: str) -> str:
    context_text = build_context_from_docs(docs)
    ea = existing_answer or "No prior answer was provided; rely on the retrieved context."
    return EMAIL_DRAFT_PROMPT.format(
        context=context_text,
        question=question,
        existing_answer=ea,
        audience=audience,
        tone=tone,
    )


def build_checklist_prompt(question: str, docs, existing_answer: str) -> str:
    context_text = build_context_from_docs(docs)
    ea = existing_answer or "No prior answer was provided; rely on the retrieved context."
    return CHECKLIST_PROMPT.format(
        context=context_text,
        question=question,
        existing_answer=ea,
    )


def build_document_review_prompt(question: str, docs, existing_answer: str) -> str:
    context_text = build_context_from_docs(docs)
    ea = existing_answer or "No prior answer was provided; rely on the retrieved context."
    return DOCUMENT_REVIEW_PROMPT.format(
        context=context_text,
        question=question,
        existing_answer=ea,
    )


def build_case_comparison_prompt(question: str, docs, existing_answer: str) -> str:
    context_text = build_context_from_docs(docs)
    ea = existing_answer or "No prior answer was provided; rely on the retrieved context."
    return CASE_COMPARISON_PROMPT.format(
        context=context_text,
        question=question,
        existing_answer=ea,
    )


def build_argumentative_lawyer_prompt(question: str, docs, existing_answer: str) -> str:
    context_text = build_context_from_docs(docs)
    ea = existing_answer or "No prior written analysis was provided; rely on the retrieved context and user's description."
    return ARGUMENTATIVE_LAWYER_PROMPT.format(
        context=context_text,
        question=question,
        existing_answer=ea,
    )

# ---------------------------------------------------------
# Retrieval logging helper
# ---------------------------------------------------------

def retrieve_and_log(user_query: str):
    """
    Uses the retriever to fetch docs and logs them.
    Returns: list[Document]
    """
    print("\n" + "=" * 70)
    print(f"🔎 RAG retrieval for query: {user_query!r}")
    try:
        docs = retriever.get_relevant_documents(user_query)
    except Exception:
        print("❌ ERROR calling retriever.get_relevant_documents:\n")
        traceback.print_exc()
        print("=" * 70 + "\n")
        return []

    if not docs:
        print("⚠️  No documents retrieved from vector index.")
        print("=" * 70 + "\n")
        return []

    for i, d in enumerate(docs, start=1):
        preview = d.page_content[:240].replace("\n", " ")
        print(f"\n[{i}] Preview: {preview!r}")
        print(f"    Metadata: {d.metadata}")

    print("=" * 70 + "\n")
    return docs


# ---------------------------------------------------------
# Flask app + API
# ---------------------------------------------------------
# Serve built React from frontend/dist
STATIC_DIR = BASE_DIR / "frontend" / "dist"

app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path="/",
)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Core RAG Q&A endpoint."""
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or data.get("query") or "").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/chat called by user_id={user_id}, user_name={user_name}")
    print(f"   Query: {user_input!r}")

    if not user_input:
        return jsonify({"answer": "Please type a question so I can help."}), 400

    try:
        docs = retrieve_and_log(user_input)
        prompt = build_prompt(user_input, docs)
        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Answer generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/chat:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I ran into an internal error while processing that query. "
            "The server logs now contain the full traceback and retrieval details. "
            "Please try again in a bit."
        )
        return jsonify({"answer": safe_msg})


@app.route("/api/draft_email", methods=["POST"])
def api_draft_email():
    """
    Agentic flow 1: draft a client email from the situation + latest analysis.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("query") or "").strip()
    existing_answer = (data.get("existing_answer") or "").strip()
    audience = (data.get("audience") or "client").strip()
    tone = (data.get("tone") or "neutral professional").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/draft_email called by user_id={user_id}, user_name={user_name}")
    print(f"   Question: {question!r}")
    print(f"   Audience: {audience!r}, tone: {tone!r}")

    if not question and not existing_answer:
        return jsonify(
            {
                "answer": "I need at least a question or some existing analysis to draft an email."
            }
        ), 400

    try:
        # If question is empty, fall back to using existing answer text as query
        retrieval_query = question or existing_answer[:2000]
        docs = retrieve_and_log(retrieval_query)

        prompt = build_email_prompt(
            question=question or "Use the analysis above to draft an appropriate email.",
            docs=docs,
            existing_answer=existing_answer,
            audience=audience,
            tone=tone,
        )

        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Email draft generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/draft_email:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I wasn't able to generate the email draft due to an internal error. "
            "Please try again after a moment or slightly rephrase your request."
        )
        return jsonify({"answer": safe_msg})


@app.route("/api/checklist", methods=["POST"])
def api_checklist():
    """
    Agentic flow 2: generate a legal checklist from the situation + analysis.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("query") or "").strip()
    existing_answer = (data.get("existing_answer") or "").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/checklist called by user_id={user_id}, user_name={user_name}")
    print(f"   Question: {question!r}")

    if not question and not existing_answer:
        return jsonify(
            {
                "answer": "I need at least a question or some existing analysis to build a checklist."
            }
        ), 400

    try:
        retrieval_query = question or existing_answer[:2000]
        docs = retrieve_and_log(retrieval_query)

        prompt = build_checklist_prompt(
            question=question or "Use the analysis above to derive a checklist.",
            docs=docs,
            existing_answer=existing_answer,
        )

        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Checklist generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/checklist:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I wasn't able to generate the checklist due to an internal error. "
            "Please try again after a moment or slightly rephrase your request."
        )
        return jsonify({"answer": safe_msg})


@app.route("/api/document_review", methods=["POST"])
def api_document_review():
    """
    Agentic flow 3: review a document / situation using retrieved law + latest analysis.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("query") or "").strip()
    existing_answer = (data.get("existing_answer") or "").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/document_review called by user_id={user_id}, user_name={user_name}")
    print(f"   Question: {question!r}")

    if not question and not existing_answer:
        return jsonify(
            {
                "answer": "I need at least a document description or some existing analysis to review."
            }
        ), 400

    try:
        # If question is empty, fall back to existing answer text for retrieval
        retrieval_query = question or existing_answer[:2000]
        docs = retrieve_and_log(retrieval_query)

        prompt = build_document_review_prompt(
            question=question or "Use the analysis above to review the document or situation.",
            docs=docs,
            existing_answer=existing_answer,
        )

        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Document review generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/document_review:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I wasn't able to complete the document review due to an internal error. "
            "Please try again after a moment or slightly rephrase your request."
        )
        return jsonify({"answer": safe_msg})


@app.route("/api/case_comparison", methods=["POST"])
def api_case_comparison():
    """
    Agentic flow 4: compare the user's situation with similar cases from the retrieved context.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("query") or "").strip()
    existing_answer = (data.get("existing_answer") or "").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/case_comparison called by user_id={user_id}, user_name={user_name}")
    print(f"   Question: {question!r}")

    if not question and not existing_answer:
        return jsonify(
            {
                "answer": "I need at least a description of your situation or some existing analysis to compare with cases."
            }
        ), 400

    try:
        retrieval_query = question or existing_answer[:2000]
        docs = retrieve_and_log(retrieval_query)

        prompt = build_case_comparison_prompt(
            question=question or "Use the analysis above to compare with similar cases.",
            docs=docs,
            existing_answer=existing_answer,
        )

        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Case comparison generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/case_comparison:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I wasn't able to complete the case comparison due to an internal error. "
            "Please try again after a moment or slightly rephrase your request."
        )
        return jsonify({"answer": safe_msg})


@app.route("/api/argumentative_lawyer", methods=["POST"])
def api_argumentative_lawyer():
    """
    Agentic flow 5: build strong prosecution & defence style arguments.
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("query") or "").strip()
    existing_answer = (data.get("existing_answer") or "").strip()
    user_id = data.get("user_id") or "anonymous"
    user_name = data.get("user_name") or "User"

    print(f"\n📨 /api/argumentative_lawyer called by user_id={user_id}, user_name={user_name}")
    print(f"   Question: {question!r}")

    if not question and not existing_answer:
        return jsonify(
            {
                "answer": (
                    "I need at least your question or the last analysis to build arguments. "
                    "Please ask about your situation first, then run this agent."
                )
            }
        ), 400

    try:
        retrieval_query = question or existing_answer[:2000]
        docs = retrieve_and_log(retrieval_query)

        prompt = build_argumentative_lawyer_prompt(
            question=question or "Use the analysis above and build prosecution and defence style arguments.",
            docs=docs,
            existing_answer=existing_answer,
        )

        res = llm.invoke(prompt)
        answer = getattr(res, "content", str(res))

        print("✅ Argumentative lawyer outline generated successfully.\n")
        return jsonify({"answer": answer})

    except Exception:
        print("❌ ERROR in /api/argumentative_lawyer:")
        traceback.print_exc()
        safe_msg = (
            "Bharat LawBot\n\n"
            "I wasn't able to complete the argument outline due to an internal error. "
            "Please try again after a moment or slightly rephrase your request."
        )
        return jsonify({"answer": safe_msg})


# ---------------------------------------------------------
# Static file routes (serve React single page)
# ---------------------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    # If file exists in dist, serve it; otherwise serve index.html for SPA routing
    file_path = STATIC_DIR / path
    if path and file_path.exists():
        return send_from_directory(STATIC_DIR, path)
    return send_from_directory(STATIC_DIR, "index.html")


if __name__ == "__main__":
    # 0.0.0.0 + port 8080 to match what you were using
    app.run(host="0.0.0.0", port=8080, debug=True)
