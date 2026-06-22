import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowUp } from "lucide-react";
import { Button } from "./ui/button";

const SUGGESTIONS = [
  "What’s my day like?",
  "When should I leave?",
  "Any important emails?",
  "What did I miss?",
];

export function CommandBar({ compact = false }) {
  const [q, setQ] = useState("");
  const navigate = useNavigate();

  const send = (text) => {
    const message = (text ?? q).trim();
    if (!message) return;
    navigate("/talk", { state: { initialMessage: message } });
    setQ("");
  };

  return (
    <div className="w-full">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="glass flex items-center gap-2 rounded-full pl-4 pr-2 py-2 focus-within:shadow-[var(--kaelra-focus)]"
      >
        <Sparkles size={18} className="text-[hsl(var(--primary))] shrink-0" />
        <input
          data-testid="global-command-bar-input"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ask Kaelra what matters today…"
          className="flex-1 bg-transparent border-0 outline-none text-sm md:text-base placeholder:text-muted-foreground"
        />
        <Button
          data-testid="global-command-bar-submit-button"
          type="submit"
          size="icon"
          className="h-9 w-9 rounded-full shrink-0"
          aria-label="Ask Kaelra"
        >
          <ArrowUp size={16} />
        </Button>
      </form>
      {!compact && (
        <div className="mt-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              data-testid="global-command-bar-suggestion-chip"
              onClick={() => send(s)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
