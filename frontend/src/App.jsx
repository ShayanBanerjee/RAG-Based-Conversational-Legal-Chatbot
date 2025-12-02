import React, { useState, useEffect, useRef } from "react";
import ChatMessage from "./components/ChatMessage.jsx";
import SuggestionChips from "./components/SuggestionChips.jsx";

const SUGGESTIONS = [
  "What are my rights if my landlord is not returning my security deposit?",
  "How can I file an FIR for online fraud in India?",
  "What is the basic process of divorce under Indian law?",
  "What should I do if I receive a legal notice from my employer?",
  "What are my rights if I am harassed at the workplace?"
];

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      text:
        "Namaste 👋, I am Bharat Law Bot — your legal help assistant for Indian law. " +
        "Ask me in simple language and I’ll help you understand your rights. " +
        "This is for information only and does not replace a qualified lawyer."
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [theme, setTheme] = useState("dark"); // "dark" | "light"

  const chatEndRef = useRef(null);

  useEffect(() => {
    document.title = "Bharat Law Bot – India’s Legal Help Chatbot";
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading]);

  const handleSend = async (text) => {
    const trimmed = (text ?? input).trim();
    if (!trimmed || isLoading) return;

    const userMsg = {
      id: Date.now() + "-user",
      role: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();

      const botMsg = {
        id: Date.now() + "-bot",
        role: "assistant",
        text:
          data.response ||
          "Sorry, I could not understand that. Please try again in a different way.",
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("Error calling backend:", err);
      const errorMsg = {
        id: Date.now() + "-error",
        role: "assistant",
        text:
          "I’m facing some technical issue right now. Please try again in a while or consult a qualified lawyer.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const hasUserAsked = messages.some((m) => m.role === "user");

  return (
    <div className={`bharatlaw-root theme-${theme}`}>
      <div className="blb-background" />

      <header className="blb-header">
        <div className="blb-logo">
          <span className="blb-logo-icon">⚖️</span>
          <div className="blb-logo-text">
            <span className="blb-logo-title">Bharat Law Bot</span>
            <span className="blb-logo-subtitle">India’s Legal Help Chatbot</span>
          </div>
        </div>

        <div className="blb-header-right">
          <button
            className="blb-theme-toggle"
            type="button"
            onClick={toggleTheme}
          >
            {theme === "dark" ? "☀️ Light" : "🌙 Dark"}
          </button>
        </div>
      </header>

      <main className="blb-main">
        <section className="blb-chat-panel">
          {!hasUserAsked && (
            <div className="blb-hero">
              <h1 className="blb-hero-title">
                Get clear, simple answers on Indian law.
              </h1>
              <p className="blb-hero-subtitle">
                Ask about your rights at work, home, online, and more. 
                Bharat Law Bot explains laws in easy language.
              </p>

              <SuggestionChips
                suggestions={SUGGESTIONS}
                onClickSuggestion={handleSuggestionClick}
              />
            </div>
          )}

          <div className="blb-chat-window">
            {messages.map((m) => (
              <ChatMessage key={m.id} role={m.role} text={m.text} />
            ))}

            {isLoading && (
              <div className="blb-typing-indicator">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <form className="blb-input-bar" onSubmit={handleSubmit}>
            <textarea
              rows={1}
              className="blb-input"
              placeholder="Describe your situation or question about Indian law..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              type="submit"
              className="blb-send-btn"
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? "Thinking..." : "Send"}
            </button>
          </form>

          <p className="blb-disclaimer">
            ⚠️ Bharat Law Bot provides general legal information based on Indian
            law and is not a substitute for professional legal advice or representation.
          </p>
        </section>
      </main>
    </div>
  );
}
