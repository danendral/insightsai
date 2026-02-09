/**
 * QueryPanel Component - Natural Language Query Interface
 *
 * KEY CONCEPT - Controlled Components:
 * In React, form inputs can be "controlled" — their value is stored in state
 * and updated via onChange. This gives us full control over the input.
 *
 * KEY CONCEPT - async/await in React:
 * We use async functions inside event handlers to call the API.
 * While waiting, we show a loading spinner.
 */

import { useState } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { queryData } from "@/lib/api";

const SUGGESTED_QUESTIONS = [
  "What was the best performing month by revenue?",
  "Which product category generates the most revenue?",
  "How does marketing spend correlate with revenue?",
  "What region has the highest conversion rate?",
  "Compare Q3 vs Q4 performance",
  "What campaign had the best ROI?",
];

export default function QueryPanel() {
  const [question, setQuestion] = useState("");
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (q) => {
    const text = q || question.trim();
    if (!text) return;

    setLoading(true);
    setError(null);
    setQuestion("");

    // Add the question to the conversation immediately
    setConversations((prev) => [...prev, { type: "question", text }]);

    try {
      const result = await queryData(text);
      setConversations((prev) => [
        ...prev,
        { type: "answer", text: result.answer },
      ]);
    } catch (err) {
      setError(err.message);
      setConversations((prev) => [
        ...prev,
        { type: "error", text: err.message },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="space-y-6">
      {/* Suggested questions */}
      <div className="bg-surface rounded-xl border border-border p-5">
        <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          Try asking
        </h3>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleSubmit(q)}
              disabled={loading}
              className="text-xs px-3 py-1.5 bg-surface-alt border border-border rounded-full hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation history */}
      {conversations.length > 0 && (
        <div className="space-y-4">
          {conversations.map((msg, i) => (
            <div
              key={i}
              className={`rounded-xl p-4 ${
                msg.type === "question"
                  ? "bg-primary/5 border border-primary/20 ml-8"
                  : msg.type === "error"
                  ? "bg-red-50 border border-red-200 mr-8"
                  : "bg-surface border border-border mr-8"
              }`}
            >
              <p className="text-xs font-medium text-text-muted mb-1">
                {msg.type === "question" ? "You" : msg.type === "error" ? "Error" : "InsightsAI"}
              </p>
              <p className="text-sm text-text whitespace-pre-wrap">{msg.text}</p>
            </div>
          ))}

          {loading && (
            <div className="bg-surface border border-border rounded-xl p-4 mr-8">
              <p className="text-xs font-medium text-text-muted mb-1">InsightsAI</p>
              <div className="flex items-center gap-2 text-sm text-text-muted">
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing your data...
              </div>
            </div>
          )}
        </div>
      )}

      {/* Input area */}
      <div className="bg-surface rounded-xl border border-border p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your data..."
            disabled={loading}
            className="flex-1 px-4 py-2 bg-surface-alt border border-border rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary disabled:opacity-50"
          />
          <button
            onClick={() => handleSubmit()}
            disabled={loading || !question.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-medium rounded-lg hover:bg-primary-hover disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
            Ask
          </button>
        </div>
        {error && !conversations.find((c) => c.type === "error" && c.text === error) && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>
    </div>
  );
}
