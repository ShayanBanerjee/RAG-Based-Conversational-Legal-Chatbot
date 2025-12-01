import React from "react";

export default function ChatMessage({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`blb-message-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && (
        <div className="blb-avatar assistant">
          <span>⚖️</span>
        </div>
      )}
      {isUser && (
        <div className="blb-avatar user">
          <span>🧑</span>
        </div>
      )}

      <div className={`blb-message-bubble ${isUser ? "user" : "assistant"}`}>
        {text.split("\n").map((line, idx) => (
          <p key={idx} className="blb-message-line">
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}
