# src/agents/agentic_manager.py

from dotenv import load_dotenv
import os
from typing import Optional, Dict

from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

from src.services.retriever import retrieve_context
from src.services.summarizer import summarize_text

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# --------- Per-user conversational memory --------- #

_global_memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True
)
_user_memories: Dict[str, ConversationBufferMemory] = {}


def _get_memory_for_user(user_id: Optional[str]) -> ConversationBufferMemory:
    if not user_id:
        return _global_memory

    key = str(user_id)
    memory = _user_memories.get(key)
    if memory is None:
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        _user_memories[key] = memory
    return memory


# ---------------------- Tools ---------------------- #

def context_retriever_tool(query: str) -> str:
    """
    Use the existing Pinecone-based retriever to get context for a query.
    """
    chunks = retrieve_context(query)
    if not chunks:
        return "No relevant legal documents were found in the current index."

    combined = "\n\n---\n\n".join(chunks)
    return combined


def summarization_tool(text: str) -> str:
    """
    Summarize retrieved legal text into a structured explanation.
    """
    return summarize_text(text)


tools = [
    Tool(
        name="LegalContextRetriever",
        func=context_retriever_tool,
        description=(
            "Use this to fetch relevant sections from the legal knowledge base "
            "when the user asks about any law, section, act, or judgement."
        ),
    ),
    Tool(
        name="LegalSummarizer",
        func=summarization_tool,
        description=(
            "Use this to summarize long or complex legal passages into a clear, "
            "structured explanation for the user."
        ),
    ),
]


def _get_llm():
    # Use a model that supports 'stop' parameter with LangChain agents
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
    )


def get_agentic_chain(user_id: Optional[str] = None):
    llm = _get_llm()
    memory = _get_memory_for_user(user_id)

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
    )
    return agent


def agentic_response(query: str, user_id: Optional[str] = None) -> str:
    """
    Main entry for agentic reasoning:
    - Uses per-user conversation memory
    - Calls tools (retriever + summarizer) as needed
    - Returns a final natural language answer
    """
    agent = get_agentic_chain(user_id=user_id)
    result = agent.run(query)
    return result
