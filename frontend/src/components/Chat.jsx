import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  Sparkles,
  Send,
  Loader2,
  Mail,
  ListChecks,
  FileText,
  Scale,
  Download,
  Trash2,        
} from "lucide-react";
import MessageBubble from "./MessageBubble";

const PROMPT_GROUPS = [
  {
    category: "Criminal law",
    prompts: [
      "Summarize Section 420 IPC in simple language.",
      "What are the key ingredients of cheating under Indian law?",
      "Explain the difference between bailable and non-bailable offences.",
    ],
  },
  {
    category: "Contracts & commercial",
    prompts: [
      "What clauses are important in an NDA under Indian law?",
      "List key risk clauses in a typical services agreement.",
      "Explain limitation of liability in simple terms.",
    ],
  },
  {
    category: "Employment & labour",
    prompts: [
      "Compare rights of an employee vs consultant under Indian law.",
      "Explain notice period and severance obligations for termination.",
      "What should a basic employment contract include?",
    ],
  },
  {
    category: "Property & tenancy",
    prompts: [
      "Explain consequences of delayed rent payment in a rental agreement.",
      "What are essential clauses in a commercial lease?",
      "How does security deposit typically work in residential tenancy?",
    ],
  },
];

// Compact agent pill with tooltip + subtle hover
function AgentCard({ icon, title, subtitle, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={subtitle} // native tooltip with extra details
      className="inline-flex w-full items-center justify-between gap-2 rounded-full border border-accentSoft bg-softbg px-3 py-1.5 text-[11px] font-medium text-gray-800 hover:bg-accentSoft hover:text-accent transition disabled:opacity-50 disabled:cursor-not-allowed group"
    >
      <span className="inline-flex items-center gap-1.5">
        <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/80 text-accent group-hover:scale-105 group-hover:shadow-sm transition">
          {icon}
        </span>
        <span>{title}</span>
      </span>
      <Sparkles
        size={13}
        className="text-accent/70 group-hover:text-accent group-hover:animate-pulse"
      />
    </button>
  );
}

export default function Chat({ user }) {
  const userId = user?.id || "guest";
  const emailKey = user?.email?.trim().toLowerCase() || null;
  const displayName =
    user?.name ||
    (emailKey && emailKey.includes("@") ? emailKey.split("@")[0] : null) ||
    "Guest";

  // Persist history by email if available, otherwise by userId
  const storageKey = emailKey
    ? `lawbot_history_email_${emailKey}`
    : `lawbot_history_${userId}`;

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const messagesEndRef = useRef(null);

  // Load history for this user/email
  useEffect(() => {
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      setMessages(JSON.parse(raw));
    } else {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            `👋 Hi **${displayName}**! I’m *Bharat LawBot*, your legal research assistant.\n\n` +
            `I use Retrieval-Augmented Generation on your legal corpora and public references to:\n\n` +
            `- Break down sections, clauses, and case law into plain language\n` +
            `- Highlight key obligations, risks, and timelines\n` +
            `- Suggest follow-up questions and next actions\n\n` +
            `I’m not a lawyer and don’t provide professional legal advice — but I can help you understand the landscape so you can have a more informed conversation with your counsel.`,
        },
      ]);
    }
  }, [storageKey, displayName]);

  // Persist per-user/email history
  useEffect(() => {
    localStorage.setItem(storageKey, JSON.stringify(messages));
  }, [messages, storageKey]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const sendQuery = async (text) => {
    const queryText = text.trim();
    if (!queryText) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user",
      content: queryText,
    };
    const withUser = [...messages, userMsg];
    setMessages(withUser);
    setInput("");
    setBusy(true);

    try {
      const res = await axios.post("/api/chat", {
        query: queryText,
        user_id: userId,
        user_name: displayName,
      });

      const answer =
        res.data?.answer ||
        "I couldn't generate a response due to an internal error. Please try again.";

      const botMsg = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: answer,
      };
      setMessages([...withUser, botMsg]);
    } catch (err) {
      console.error(err);
      const botMsg = {
        id: `assistant-error-${Date.now()}`,
        role: "assistant",
        content:
          "Bharat LawBot\n\nSorry, I ran into an internal error while processing that. Please try again in a bit.",
      };
      setMessages([...withUser, botMsg]);
    } finally {
      setBusy(false);
    }
  };

  const onSubmit = (e) => {
    e.preventDefault();
    if (!busy) sendQuery(input);
  };

  const usePrompt = (p) => {
    if (!busy) sendQuery(p);
  };

  // --- Clear chat for this user/email and restore welcome bubble ---
  const handleClearChat = () => {
    const confirmed = window.confirm(
      "Clear the current conversation? This cannot be undone."
    );
    if (!confirmed) return;

    try {
      localStorage.removeItem(storageKey);
    } catch (err) {
      console.warn("Failed to clear stored chat history:", err);
    }

    // restore just the initial welcome message
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content:
          `👋 Namaste! I’m **Bharat LawBot**, your AI assistant for Indian law.\n\n` +
          `You can ask me about:\n\n` +
          `Contracts, employment & labour, property, criminal procedure\n` +
          `Notices, replies, basic compliance checks\n` +
          `“What does Section X of Y Act mean in simple words?”\n\n` +
          `> **Disclaimer:** I provide general legal information only and do **not** replace a qualified advocate.`,
      },
    ]);
  };

  // --- Export current chat as a Markdown file (keeps formatting) ---
  const handleExportChat = () => {
    if (!messages || messages.length === 0) {
      window.alert("No messages to export yet.");
      return;
    }

    const lines = messages.map((m) => {
      const who = m.role === "user" ? "User" : "Bharat LawBot";
      return `### ${who}\n\n${m.content}`;
    });

    const content =
      `# Bharat LawBot – Chat Export\n\n` +
      `Exported on: ${new Date().toLocaleString()}\n\n` +
      lines.join("\n\n---\n\n");

    const blob = new Blob([content], {
      type: "text/markdown;charset=utf-8;",
    });

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    const safeName =
      (emailKey || displayName || "guest").toString().replace(
        /[^a-z0-9\-_.@]/gi,
        "_"
      ) || "guest";

    a.href = url;
    a.download = `bharat-lawbot-chat-${safeName}-${new Date()
      .toISOString()
      .slice(0, 19)
      .replace(/[:T]/g, "-")}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const getLastContext = () => {
    let lastUser = null;
    let lastAssistant = null;

    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const m = messages[i];
      if (!lastAssistant && m.role === "assistant") {
        lastAssistant = m;
      } else if (!lastUser && m.role === "user") {
        lastUser = m;
      }
      if (lastUser && lastAssistant) break;
    }

    return { lastUser, lastAssistant };
  };

  const callAgentEndpoint = async (endpoint, extraPayload = {}) => {
    if (busy) return;

    const { lastUser, lastAssistant } = getLastContext();
    if (!lastUser || !lastAssistant) {
      const botMsg = {
        id: `assistant-helper-${Date.now()}`,
        role: "assistant",
        content:
          "To use this feature, please ask a legal question first so I can analyse it and then create a draft, checklist, or analysis from that answer.",
      };
      setMessages([...messages, botMsg]);
      return;
    }

    setBusy(true);
    try {
      const res = await axios.post(endpoint, {
        query: lastUser.content,
        existing_answer: lastAssistant.content,
        user_id: userId,
        user_name: displayName,
        ...extraPayload,
      });

      const answer =
        res.data?.answer ||
        "I couldn't generate a response due to an internal error. Please try again.";

      const botMsg = {
        id: `assistant-agent-${Date.now()}`,
        role: "assistant",
        content: answer,
      };
      setMessages([...messages, botMsg]);
    } catch (err) {
      console.error(err);
      const botMsg = {
        id: `assistant-agent-error-${Date.now()}`,
        role: "assistant",
        content:
          "Bharat LawBot\n\nI couldn't complete that agentic action due to an internal error. Please try again in a bit.",
      };
      setMessages([...messages, botMsg]);
    } finally {
      setBusy(false);
    }
  };

  const handleDraftEmail = () => {
    callAgentEndpoint("/api/draft_email", {
      audience: "client",
      tone: "neutral professional",
    });
  };

  const handleChecklist = () => {
    callAgentEndpoint("/api/checklist");
  };

  const handleDocumentReview = () => {
    callAgentEndpoint("/api/document_review");
  };

  const handleCaseComparison = () => {
    callAgentEndpoint("/api/case_comparison");
  };

  const handleArgumentativeLawyer = () => {
    callAgentEndpoint("/api/argumentative_lawyer");
  };

  return (
    <div className="w-full h-full flex gap-3 md:gap-4">
      {/* Left panel: Agents + prompt bubbles */}
      <aside className="hidden md:flex md:w-60 flex-col space-y-3 text-[11px] overflow-y-auto scroll-thin pr-1">
        {/* Agents section */}
        <div className="bg-white/90 rounded-2xl shadow-soft border border-white/60 p-3 pb-2">
          <p className="font-semibold text-gray-800 mb-1 text-[10px] uppercase tracking-wide">
            Agents
          </p>
          <p className="text-[10px] text-gray-500 mb-2">
            One-click actions on your latest answer.
          </p>
          <div className="flex flex-col gap-1">
            <AgentCard
              title="Draft client email"
              subtitle="Turn this answer into a polite, client-ready email."
              onClick={handleDraftEmail}
              disabled={busy}
              icon={<Mail size={12} />}
            />
            <AgentCard
              title="Create checklist"
              subtitle="Extract action items and next steps you shouldn’t miss."
              onClick={handleChecklist}
              disabled={busy}
              icon={<ListChecks size={12} />}
            />
            <AgentCard
              title="Review document"
              subtitle="Highlight protections, risks and missing clauses."
              onClick={handleDocumentReview}
              disabled={busy}
              icon={<FileText size={12} />}
            />
            <AgentCard
              title="Compare similar cases"
              subtitle="See how your situation lines up with other cases."
              onClick={handleCaseComparison}
              disabled={busy}
              icon={<Scale size={12} />}
            />
            <AgentCard
              title="Build arguments (for & against)"
              subtitle="Get strong prosecution and defence-style arguments."
              onClick={handleArgumentativeLawyer}
              disabled={busy}
              icon={<Scale size={12} className="rotate-90" />}
            />
          </div>
        </div>

        {/* Prompts section header */}
        <p className="font-semibold text-gray-500 mt-1 text-[10px] uppercase tracking-wide">
          Quick prompts
        </p>

        {/* Prompt bubble groups */}
        {PROMPT_GROUPS.map((group) => (
          <div
            key={group.category}
            className="bg-white/80 rounded-2xl shadow-soft border border-white/60 p-3"
          >
            <p className="font-semibold text-gray-800 mb-2">
              {group.category}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {group.prompts.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => usePrompt(p)}
                  className="px-2.5 py-1 rounded-full bg-softbg hover:bg-accentSoft hover:text-accent transition border border-accentSoft text-left"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ))}
      </aside>

      {/* Right: chat card fills remaining height */}
      <section className="flex-1 flex">
        <div className="w-full bg-white shadow-soft rounded-3xl p-4 md:p-5 flex flex-col h-full">
          {/* Header (compact to maximise chat area) */}
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
                <Sparkles className="text-accent" size={18} />
                Bharat LawBot
              </div>
              <p className="text-xs text-gray-500">
                Copilot-style, RAG-enhanced legal assistant for Indian law.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <p className="hidden sm:block text-[11px] text-gray-400">
                Chats are saved locally for this profile.
              </p>
              <button
                type="button"
                onClick={handleExportChat}
                className="inline-flex items-center gap-1.5 rounded-full border border-softbg px-2.5 py-1 text-[11px] text-gray-700 hover:bg-softbg hover:text-gray-900 transition"
              >
                <Download size={12} />
                Export
              </button>
              <button
                type="button"
                onClick={handleClearChat}
                className="inline-flex items-center gap-1.5 rounded-full border border-red-100 px-2.5 py-1 text-[11px] text-red-600 hover:bg-red-50 hover:text-red-700 transition"
              >
                <Trash2 size={12} />
                Clear
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 rounded-2xl bg-softbg/60 border border-softbg overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto scroll-thin px-3 py-3 space-y-3 md:space-y-4">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}

              {/* Typing indicator when busy */}
              {busy && (
                <div className="flex justify-start">
                  <div className="typing-indicator mt-1">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input – stays pinned, big text area overall */}
          <form
            onSubmit={onSubmit}
            className="mt-3 flex gap-2 items-center text-sm"
          >
            <div className="flex-1 flex items-center gap-2 bg-white border border-softbg rounded-full px-3 py-1.5 shadow-sm">
              <textarea
                rows={1}
                className="flex-1 resize-none border-none outline-none text-sm bg-transparent max-h-24"
                placeholder="Ask about a section, clause, or situation…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (!busy) sendQuery(input);
                  }
                }}
              />
            </div>
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="inline-flex items-center justify-center rounded-full bg-accent text-white px-3 py-2 text-xs md:text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition"
            >
              {busy ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Send size={16} />
              )}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
