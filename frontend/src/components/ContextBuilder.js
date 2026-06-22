import React, { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { KaelraOrb } from "./KaelraOrb";
import { Button } from "./ui/button";
import {
  CalendarDays, Mail, FolderOpen, Brain, ListChecks, ShieldCheck, ArrowRight,
} from "lucide-react";

const STEPS = [
  "Give me a moment — I'm learning what matters to you.",
  "I'm organizing your context.",
  "I'm finding important files, routines, deadlines, and people.",
  "I'm preparing your first personal briefing.",
  "Your Kaelra context is ready.",
];

const SOURCE_LABEL = {
  google_calendar: "Calendar",
  gmail: "Gmail",
  google_drive: "Drive",
  maps: "Maps",
  news: "News",
};

/**
 * Context Builder experience. On mount it animates Kaelra's indexing progress
 * while POST /context/build runs, then shows a summary of what she indexed.
 * Kaelra only ever references the sources the user actually connected.
 */
export function ContextBuilder({ onDone, doneLabel = "Enter Kaelra" }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    let mounted = true;
    let i = 0;
    const interval = setInterval(() => {
      i = Math.min(i + 1, STEPS.length - 2);
      if (mounted) setStepIdx(i);
    }, 1400);
    (async () => {
      try {
        const { data } = await api.post("/context/build");
        if (mounted) setSummary(data);
      } catch (e) {
        if (mounted) setError("Kaelra couldn't finish indexing right now — you can rebuild from Settings.");
      } finally {
        clearInterval(interval);
        if (mounted) setStepIdx(STEPS.length - 1);
      }
    })();
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const done = !!(summary || error);
  const indexed = summary?.indexed || { events: 0, emails: 0, files: 0 };
  const sources = summary?.sources || [];

  const stat = (icon, value, label) => (
    <div className="flex flex-col items-center rounded-xl border border-white/10 bg-white/5 px-3 py-3">
      <span className="text-[hsl(var(--primary))]">{icon}</span>
      <span className="mt-1 font-heading text-xl">{value}</span>
      <span className="text-[11px] text-muted-foreground">{label}</span>
    </div>
  );

  return (
    <div className="flex flex-col items-center text-center" data-testid="context-builder">
      <KaelraOrb size={112} state={done && !error ? "speaking" : "thinking"} />

      {!done && (
        <div className="mt-6 min-h-[64px]">
          <p key={stepIdx} className="font-heading text-lg kaelra-fade-up" data-testid="context-builder-step">
            {STEPS[stepIdx]}
          </p>
          <div className="mt-4 flex items-center justify-center gap-1.5">
            {STEPS.map((_, idx) => (
              <span key={idx}
                className={`h-1.5 rounded-full transition-all ${idx <= stepIdx ? "w-6 bg-[hsl(var(--primary))]" : "w-1.5 bg-white/15"}`} />
            ))}
          </div>
        </div>
      )}

      {done && error && (
        <div className="mt-6">
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button className="mt-5" onClick={onDone} data-testid="context-builder-done">{doneLabel}</Button>
        </div>
      )}

      {done && !error && summary && (
        <div className="mt-6 w-full kaelra-fade-up">
          <p className="font-heading text-xl">Your Kaelra context is ready.</p>
          <p className="mt-1 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
            <ShieldCheck size={13} className="text-[hsl(var(--primary))]" />
            I searched only the sources you connected{sources.length ? `: ${sources.map((s) => SOURCE_LABEL[s] || s).join(", ")}` : ""}.
          </p>

          <div className="mt-5 grid grid-cols-3 gap-2">
            {stat(<CalendarDays size={18} />, indexed.events, "events")}
            {stat(<Mail size={18} />, indexed.emails, "emails")}
            {stat(<FolderOpen size={18} />, indexed.files, "files")}
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2">
            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-left">
              <Brain size={16} className="text-[hsl(var(--primary))] shrink-0" />
              <span className="text-sm"><b className="font-heading">{summary.suggested_memories || 0}</b> memories to review</span>
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-left">
              <ListChecks size={16} className="text-[hsl(var(--primary))] shrink-0" />
              <span className="text-sm"><b className="font-heading">{summary.actions_prepared || 0}</b> actions prepared</span>
            </div>
          </div>

          <Button className="mt-6 w-full gap-1.5" onClick={onDone} data-testid="context-builder-done">
            {doneLabel} <ArrowRight size={16} />
          </Button>
        </div>
      )}
    </div>
  );
}
