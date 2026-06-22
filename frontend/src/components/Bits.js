import React from "react";
import { KaelraOrb } from "./KaelraOrb";

export function GlassCard({ children, className = "", as: Tag = "div", ...rest }) {
  return (
    <Tag
      className={`glass transition-colors hover:bg-[var(--kaelra-glass-strong)] hover:border-white/15 ${className}`}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function SectionTitle({ kicker, title, icon: Icon, action }) {
  return (
    <div className="flex items-center justify-between gap-3 mb-3">
      <div className="flex items-center gap-2.5 min-w-0">
        {Icon && (
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]">
            <Icon size={16} />
          </span>
        )}
        <div className="min-w-0">
          {kicker && <div className="kaelra-kicker">{kicker}</div>}
          <h3 className="font-heading text-base md:text-lg truncate">{title}</h3>
        </div>
      </div>
      {action}
    </div>
  );
}

export function StatusPill({ children, tone = "default", className = "", ...rest }) {
  const tones = {
    default: "bg-white/5 text-muted-foreground border-white/10",
    teal: "bg-[rgba(45,212,191,0.14)] text-[rgb(153,246,228)] border-[rgba(45,212,191,0.22)]",
    amber: "bg-[rgba(245,158,11,0.14)] text-[rgb(253,230,138)] border-[rgba(245,158,11,0.22)]",
    sensitive: "bg-[rgba(251,146,60,0.14)] text-[rgb(254,215,170)] border-[rgba(251,146,60,0.22)]",
    green: "bg-[rgba(34,197,94,0.14)] text-[rgb(134,239,172)] border-[rgba(34,197,94,0.22)]",
    red: "bg-[rgba(239,68,68,0.14)] text-[rgb(254,202,202)] border-[rgba(239,68,68,0.22)]",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${tones[tone] || tones.default} ${className}`}
      {...rest}
    >
      {children}
    </span>
  );
}

export function LoadingState({ label = "Kaelra is checking your day…" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center" data-testid="kaelra-loading-state">
      <KaelraOrb size={84} state="thinking" />
      <p className="text-sm text-muted-foreground font-mono-k">{label}</p>
    </div>
  );
}

export function EmptyState({ title, hint, icon: Icon, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center px-6" data-testid="kaelra-empty-state">
      <KaelraOrb size={64} state="idle" />
      <div>
        <p className="font-heading text-base">{title}</p>
        {hint && <p className="text-sm text-muted-foreground mt-1 max-w-sm">{hint}</p>}
      </div>
      {action}
    </div>
  );
}
