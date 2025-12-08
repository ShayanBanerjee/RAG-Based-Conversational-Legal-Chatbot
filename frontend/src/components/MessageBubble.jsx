import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { motion } from "framer-motion";
import { Sparkles, Copy, Check } from "lucide-react";

export default function MessageBubble({ message }) {
  const isAssistant = message.role === "assistant";
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!isAssistant || !message?.content) return;
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error("Failed to copy", err);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isAssistant ? "justify-start" : "justify-end"}`}
    >
      <div
        className={`max-w-[90%] md:max-w-[80%] rounded-2xl px-3 py-2.5 md:px-4 md:py-3 text-xs md:text-sm ${
          isAssistant
            ? "bg-white border border-softbg text-gray-800 shadow-sm"
            : "bg-accent text-white rounded-br-sm"
        }`}
      >
        {isAssistant && (
          <div className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-1 text-[10px] text-accent">
              <Sparkles size={12} />
              <span>Bharat LawBot</span>
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 text-[10px] text-gray-400 hover:text-accent transition"
              title="Copy answer"
            >
              {copied ? (
                <>
                  <Check size={10} />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy size={10} />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight]}
          className="prose prose-sm max-w-none prose-p:my-1 prose-li:my-0.5 prose-strong:font-semibold"
        >
          {message.content}
        </ReactMarkdown>
      </div>
    </motion.div>
  );
}
