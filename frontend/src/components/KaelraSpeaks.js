import React, { useEffect, useRef } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { StatusPill } from "./Bits";
import { KaelraOrb } from "./KaelraOrb";
import {
  Volume2, Square, Mail, CalendarClock, FolderOpen, Bell, MapPin, VolumeX, Newspaper, ExternalLink,
} from "lucide-react";

const KIND_ICON = { email: Mail, event: CalendarClock, file: FolderOpen, note: Bell, news: Newspaper };

/**
 * "Kaelra speaks" view. When opened she auto-narrates the item aloud (unless muted,
 * in which case she writes it first and offers a play button) and shows the actual
 * email / event / file card — not a chat bubble.
 */
export function KaelraSpeaks({ item, muted, voice, onClose }) {
  const lastIdRef = useRef(null);

  useEffect(() => {
    if (item && item.id !== lastIdRef.current) {
      lastIdRef.current = item.id;
      if (!muted && voice?.speak) voice.speak(item.narration);
    }
    if (!item) lastIdRef.current = null;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item, muted]);

  if (!item) return null;
  const card = item.card || {};
  const Icon = KIND_ICON[item.kind] || Bell;
  const speaking = !!voice?.speaking;

  const togglePlay = () => {
    if (speaking) voice.stopSpeaking();
    else voice.speak(item.narration);
  };

  return (
    <Dialog open={!!item} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="glass-strong border-white/10" data-testid="kaelra-speaks">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 font-heading">
            <KaelraOrb size={40} state={speaking ? "speaking" : "idle"} />
            <div>
              <div className="text-base">Kaelra</div>
              <div className="font-mono-k text-[11px] text-muted-foreground">
                {muted ? "muted · written" : (speaking ? "speaking…" : "tap play to hear")}
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        {muted && (
          <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted-foreground" data-testid="kaelra-speaks-muted">
            <VolumeX size={14} className="text-[hsl(var(--accent))]" /> You're muted — here's what I'd say:
          </div>
        )}

        <p className="text-[15px] leading-relaxed" data-testid="kaelra-speaks-narration">{item.narration}</p>

        {/* The actual card */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-3.5" data-testid="kaelra-speaks-card">
          <div className="flex items-start gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]"><Icon size={17} /></span>
            <div className="min-w-0 flex-1">
              <div className="font-heading text-sm">{item.title}</div>
              {item.subtitle && <div className="text-xs text-muted-foreground">{item.subtitle}</div>}
            </div>
            {item.tone && item.tone !== "default" && (
              <StatusPill tone={item.tone} className="shrink-0">
                {item.kind === "email" && card.monitored ? "monitored" : item.kind}
              </StatusPill>
            )}
          </div>

          {item.kind === "email" && card.snippet && (
            <p className="mt-2.5 text-sm text-foreground/80">{card.snippet}</p>
          )}
          {item.kind === "event" && card.location && (
            <p className="mt-2.5 flex items-center gap-1.5 text-sm text-foreground/80"><MapPin size={13} /> {card.location}</p>
          )}
          {item.kind === "file" && card.reason && (
            <p className="mt-2.5 text-sm text-foreground/80">{card.reason}</p>
          )}
          {item.kind === "note" && card.body && (
            <p className="mt-2.5 text-sm text-foreground/80">{card.body}</p>
          )}
          {item.kind === "news" && (
            <div className="mt-2.5 space-y-2">
              {card.summary && <p className="text-sm text-foreground/80">{card.summary}</p>}
              {card.url && (
                <a href={card.url} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-[hsl(var(--primary))] hover:underline" data-testid="kaelra-speaks-news-link">
                  <ExternalLink size={12} /> Read the story
                </a>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button variant="secondary" className="gap-1.5" onClick={togglePlay} data-testid="kaelra-speaks-play">
            {speaking ? <><Square size={14} /> Stop</> : <><Volume2 size={15} /> {muted ? "Play anyway" : "Replay"}</>}
          </Button>
          <Button onClick={onClose} data-testid="kaelra-speaks-close">Got it</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
