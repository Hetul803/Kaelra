import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useVoice } from "../lib/voice";
import { useAuth } from "../context/AuthContext";
import { KaelraOrb } from "../components/KaelraOrb";
import { KaelraSpeaks } from "../components/KaelraSpeaks";
import { SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import {
  Volume2, VolumeX, Send, Mic, Mail, CalendarClock, FolderOpen, Bell,
  ArrowRight, Sparkles, Link2,
} from "lucide-react";

const KIND_ICON = { email: Mail, event: CalendarClock, file: FolderOpen, note: Bell };

const SUGGESTIONS = [
  "What's my day like?",
  "Any important emails?",
  "What needs my attention?",
  "What did you handle for me?",
];

export default function Kaelra() {
  const navigate = useNavigate();
  const { user, profile, refreshProfile } = useAuth();
  const voice = useVoice();
  const [feed, setFeed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [muted, setMuted] = useState(false);
  const [selected, setSelected] = useState(null);
  const greetedRef = useRef(false);
  const mutePrefRef = useRef(false);

  const load = useCallback(async () => {
    let { data } = await api.get("/feed");
    if (!data.greeting) {
      try {
        const b = await api.post("/briefing");
        data = { ...data, greeting: b.data?.briefing?.greeting };
      } catch (e) { /* ignore */ }
    }
    setFeed(data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  // Sync persisted mute preference once profile loads
  useEffect(() => {
    if (profile && !mutePrefRef.current) {
      mutePrefRef.current = true;
      setMuted(profile.voice_enabled === false);
    }
  }, [profile]);

  // Speak the greeting once (after we know the mute preference)
  useEffect(() => {
    if (!feed?.greeting || greetedRef.current || !mutePrefRef.current) return;
    greetedRef.current = true;
    if (!muted && voice?.speak) voice.speak(feed.greeting);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feed, muted]);

  const toggleMute = async () => {
    const next = !muted;
    setMuted(next);
    if (next) voice.stopSpeaking();
    else if (feed?.greeting) voice.speak(feed.greeting);
    try { await api.put("/settings", { voice_enabled: !next }); refreshProfile && refreshProfile(); } catch (e) { /* ignore */ }
  };

  const ask = (text) => {
    const message = (text ?? input).trim();
    if (!message) return;
    voice.stopSpeaking();
    navigate("/talk", { state: { initialMessage: message } });
  };

  const onMic = () => {
    voice.stopSpeaking();
    const started = voice.startListening && voice.startListening((t) => { if (t) ask(t); });
    if (!started) navigate("/talk");
  };

  const openItem = (item) => { voice.stopSpeaking(); setSelected(item); };
  const closeItem = () => { voice.stopSpeaking(); setSelected(null); };

  if (loading) return <LoadingState label="Kaelra is getting up to speed…" />;

  const items = feed?.items || [];
  const speaking = !!voice.speaking;
  const greeting = feed?.greeting || `Hi${feed?.name ? ", " + feed.name : ""}. I'm Kaelra. Connect your Google and I'll start learning what matters to you.`;

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {/* Presence + greeting */}
      <div className="glass rounded-2xl p-6 kaelra-fade-up" data-testid="kaelra-home">
        <div className="flex items-start gap-4">
          <KaelraOrb size={88} state={speaking ? "speaking" : (voice.listening ? "listening" : "idle")} />
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-2">
              <div className="kaelra-kicker">Kaelra</div>
              <Button size="icon" variant={muted ? "ghost" : "secondary"} className="h-9 w-9"
                onClick={toggleMute} data-testid="kaelra-mute-toggle"
                aria-label={muted ? "Unmute Kaelra" : "Mute Kaelra"}
                title={muted ? "Kaelra is muted" : "Kaelra speaks"}>
                {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </Button>
            </div>
            <p className="mt-1 whitespace-pre-line font-heading text-lg leading-relaxed" data-testid="kaelra-greeting">
              {greeting}
            </p>
            {muted && (
              <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                <VolumeX size={12} className="text-[hsl(var(--accent))]" /> You're muted — I'll write instead of speak.
              </p>
            )}
          </div>
        </div>

        {/* Composer */}
        <div className="mt-5 flex items-end gap-2 rounded-2xl border border-white/10 bg-white/5 p-2 focus-within:shadow-[var(--kaelra-focus)]">
          <Button size="icon" variant="ghost" className="shrink-0" onClick={onMic} data-testid="kaelra-mic" aria-label="Talk">
            <Mic size={18} className={voice.listening ? "text-[hsl(var(--primary))]" : ""} />
          </Button>
          <Textarea value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }}
            rows={1} placeholder="Ask Kaelra anything…"
            className="max-h-32 min-h-[40px] flex-1 resize-none border-0 bg-transparent focus-visible:ring-0"
            data-testid="kaelra-composer" />
          <Button size="icon" className="shrink-0 rounded-xl" disabled={!input.trim()} onClick={() => ask()} data-testid="kaelra-send" aria-label="Send">
            <Send size={17} />
          </Button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => ask(s)} data-testid="kaelra-suggestion"
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground">
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Proactive feed */}
      <div>
        <SectionTitle kicker="Right now" title="Here's what I've got for you" icon={Sparkles} />
        {items.length === 0 ? (
          <div className="glass rounded-2xl p-8 text-center" data-testid="kaelra-feed-empty">
            <Link2 size={24} className="mx-auto text-[hsl(var(--primary))]" />
            <p className="mt-3 font-heading">All quiet for now</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
              Connect your Google and I'll surface the emails, meetings and files that matter — and tell you about them here.
            </p>
            <Button variant="secondary" className="mt-4 gap-1.5" onClick={() => navigate("/accounts")} data-testid="kaelra-feed-connect">
              <Sparkles size={15} /> Connect Google
            </Button>
          </div>
        ) : (
          <div className="space-y-2" data-testid="kaelra-feed">
            {items.map((item) => {
              const Icon = KIND_ICON[item.kind] || Bell;
              return (
                <button key={item.id} onClick={() => openItem(item)} data-testid="kaelra-feed-item"
                  className="group flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3.5 text-left transition-colors hover:bg-white/10 focus-visible:shadow-[var(--kaelra-focus)]">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]"><Icon size={18} /></span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{item.title}</div>
                    <div className="truncate text-xs text-muted-foreground">{item.subtitle}</div>
                  </div>
                  {item.tone && item.tone !== "default" && (
                    <StatusPill tone={item.tone} className="shrink-0">
                      {item.kind === "email" && item.card?.monitored ? "monitored" : item.kind}
                    </StatusPill>
                  )}
                  <ArrowRight size={16} className="shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
                </button>
              );
            })}
          </div>
        )}
      </div>

      <KaelraSpeaks item={selected} muted={muted} voice={voice} onClose={closeItem} />
    </div>
  );
}
