import React from "react";
import ReactMarkdown from "react-markdown";

export default function ChatMessage({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`blb-message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`blb-avatar ${isUser ? "user" : "assistant"}`}>
        <span>{isUser ? "🧑" : "⚖️"}</span>
      </div>

      <div className={`blb-message-bubble ${isUser ? "user" : "assistant"}`}>
        <ReactMarkdown className="blb-markdown">
          {text}
        </ReactMarkdown>
      </div>
    </div>
  );
}
