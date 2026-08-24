import { Bot, Send, Sparkles } from "lucide-react";
import { useState } from "react";

const SUGGESTED = [
  "Show exceptions from last 7 days",
  "What's the auto-match rate today?",
  "Summarize pending settlements",
  "Flag transactions over $50,000",
];

export function AIAssistant() {
  const [input, setInput] = useState("");

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Assistant</h1>
          <p className="page-subtitle">Natural language interface for financial operations</p>
        </div>
        <span className="badge badge-info gap-1.5">
          <Sparkles size={11} />
          Coming in Phase 3
        </span>
      </div>

      {/* Chat shell */}
      <div className="card flex flex-col" style={{ height: "calc(100vh - 240px)", minHeight: 480 }}>
        {/* Messages area */}
        <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[var(--navy)] flex items-center justify-center">
            <Bot size={28} className="text-white" />
          </div>
          <div>
            <p className="text-base font-semibold text-[var(--text-primary)]">
              LedgerPilot AI
            </p>
            <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-md">
              Ask anything about your transactions, reconciliation status,
              exceptions, or settlements in plain English.
            </p>
          </div>

          {/* Suggested prompts */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
            {SUGGESTED.map((s) => (
              <button
                key={s}
                onClick={() => setInput(s)}
                className="text-left px-4 py-3 rounded-lg border border-[var(--border)]
                           text-sm text-[var(--text-secondary)] hover:border-[var(--accent-blue)]
                           hover:text-[var(--text-primary)] transition-colors duration-150
                           bg-[var(--bg-surface-2)]"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Input bar */}
        <div className="border-t border-[var(--border)] p-4">
          <div className="flex gap-3">
            <input
              id="ai-chat-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about reconciliation, exceptions, settlements…"
              className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--border)]
                         bg-[var(--bg-surface-2)] text-[var(--text-primary)]
                         text-sm placeholder:text-[var(--text-muted)]
                         focus:outline-none focus:ring-2 focus:ring-[var(--accent-blue)]
                         focus:border-transparent transition-all"
            />
            <button
              id="ai-chat-send"
              className="btn-primary px-4"
              disabled={!input.trim()}
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
