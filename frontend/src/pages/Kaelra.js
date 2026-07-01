import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow, parseISO } from "date-fns";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useVoice } from "../lib/voice";
import { interpretCommand, executeCommand } from "../lib/kaelraCommand";
import { useAuth } from "../context/AuthContext";
import { pushSupported, getPushState, enablePush } from "../lib/push";
import { KaelraOrb } from "../components/KaelraOrb";
import { KaelraSpeaks } from "../components/KaelraSpeaks";
import { SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Volume2, VolumeX, Send, Mic, Square, Mail, CalendarClock, FolderOpen, Bell,
  ArrowRight, Sparkles, Link2, Brain, BellRing, Activity, Cpu, Newspaper,
} from "lucide-react";

const KIND_ICON = { email: Mail, event: CalendarClock, file: FolderOpen, note: Bell, news: Newspaper };
const SOURCE_ICON = { email: Mail, drive: FolderOpen, calendar: CalendarClock };

const QUICK_INTENTS = [
  "What needs my attention today?",
  "Show me the calendar",
  "Show me my email",
  "What did you learn since yesterday?",
];

const FEED_TABS = [
  { value: "all", label: "All" },
  { value: "email", label: "Email" },
  { value: "event", label: "Calendar" },
  { value: "news", label: "News" },
  { value: "file", label: "Files" },
];

// Natural-language routing lives in ../lib/kaelraCommand (shared with the
// global KaelraPresence wake-word), so Kaelra behaves the same everywhere.

function relTime(iso) {
  if (!iso) return "";
  try { return formatDistanceToNow(parseISO(iso), { addSuffix: true }); } catch (e) { return ""; }
}

export default function Kaelra() {
  const navigate = useNavigate();
  const { profile, refreshProfile } = useAuth();
  const voice = useVoice();
  const [feed, setFeed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState("");
  const [muted, setMuted] = useState(false);
  const [selected, setSelected] = useState(null);
  const [tab, setTab] = useState("all");
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [push, setPush] = useState({ supported: false, subscribed: false });
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
  useEffect(() => { if (pushSupported()) getPushState().then(setPush); }, []);

  // Sync persisted mute preference once profile loads
  useEffect(() => {
    if (profile && !mutePrefRef.current) {
      mutePrefRef.current = true;
      setMuted(profile.voice_enabled === false);
    }
  }, [profile]);

  // Speak the greeting once per session (after we know the mute preference)
  useEffect(() => {
    if (!feed?.greeting || greetedRef.current || !mutePrefRef.current) return;
    greetedRef.current = true;
    const alreadyGreeted = sessionStorage.getItem("kaelra_greeted") === "1";
    if (!muted && !alreadyGreeted && voice?.speak) {
      sessionStorage.setItem("kaelra_greeted", "1");
      voice.speak(feed.greeting);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feed, muted]);

  // Ambient phrase rotation
  const phrases = useMemo(() => {
    const watching = feed?.watching || [];
    const base = watching.length
      ? watching.map((w) => `Watching ${w}`)
      : ["Standing by", "Ready when you are"];
    return [...base, "Learning your patterns", "Synced across your devices"];
  }, [feed]);

  useEffect(() => {
    if (phrases.length < 2) return;
    const t = setInterval(() => setPhraseIdx((i) => (i + 1) % phrases.length), 6500);
    return () => clearInterval(t);
  }, [phrases]);

  const toggleMute = async () => {
    const next = !muted;
    setMuted(next);
    if (next) voice.stopSpeaking();
    else if (feed?.greeting) voice.speak(feed.greeting);
    try { await api.put("/settings", { voice_enabled: !next }); refreshProfile && refreshProfile(); } catch (e) { /* ignore */ }
  };

  // Open a Home feed card of a given kind (used by the Entity command router).
  const openCard = (kind) => {
    const it = (feed?.items || []).find((x) => x.kind === kind);
    if (it) { voice.stopSpeaking(); setSelected(it); return true; }
    return false;
  };

  const ask = (text) => {
    const message = (text ?? input).trim();
    if (!message) return;
    voice.stopSpeaking();
    setInput("");
    // Try to operate the app locally first (free — no LLM / premium voice).
    const handled = executeCommand({
      cmd: interpretCommand(message),
      navigate,
      speak: (s) => { if (!muted) voice.speakLocal(s); },
      openCard,
      closeCard: () => setSelected(null),
      stopSpeaking: () => voice.stopSpeaking(),
    });
    if (handled) return;
    // Real reasoning -> full conversation.
    navigate("/talk", { state: { initialMessage: message } });
  };

  const onMic = () => {
    voice.stopSpeaking();
    const started = voice.startListening && voice.startListening((t) => { if (t) ask(t); });
    if (!started) navigate("/talk");
  };

  const enableAlerts = async () => {
    try {
      await enablePush();
      setPush({ supported: true, subscribed: true });
      toast.success("Alerts on — I'll reach you even when this tab is closed.");
    } catch (e) {
      if (e?.message === "denied") toast.error("Notifications were blocked in your browser.");
      else if (e?.message === "unsupported") toast.message("This browser doesn't support push alerts.");
      else toast.error("Couldn't enable alerts. Try again.");
    }
  };

  const openItem = (item) => { voice.stopSpeaking(); setSelected(item); };
  const closeItem = () => { voice.stopSpeaking(); setSelected(null); };

  if (loading) return <LoadingState label="Kaelra is coming online…" />;

  const items = feed?.items || [];
  const learned = feed?.learned || [];
  const connected = (feed?.connected || []).some((p) => ["gmail", "google_calendar", "google_drive"].includes(p));
  const speaking = !!voice.speaking;
  const orbState = speaking ? "speaking" : (voice.listening ? "listening" : "idle");
  const greeting = feed?.greeting ||
    `I'm here${feed?.name && feed.name !== "there" ? ", " + feed.name : ""}. Connect your Google and I'll start learning what matters to you.`;
  const filtered = tab === "all" ? items : items.filter((i) => i.kind === tab);

  return (
    <div className="mx-auto max-w-6xl" data-testid="kaelra-home">
      {/* Ambient status line */}
      <div className="sticky top-0 z-20 -mx-4 mb-5 border-b border-white/10 bg-[rgba(11,15,20,0.55)] px-4 backdrop-blur-md md:-mx-6 md:px-6"
        data-testid="home-ambient-status">
        <div className="flex h-11 items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(var(--primary))] opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[hsl(var(--primary))]" />
            </span>
            <AnimatePresence mode="wait">
              <motion.span key={phraseIdx} data-testid="home-ambient-status-phrase"
                initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.35 }}
                className="truncate font-mono-k text-xs text-muted-foreground">
                {phrases[phraseIdx]}
                {feed?.learned_count ? <span className="text-[hsl(var(--primary))]"> · Learned {feed.learned_count}</span> : null}
              </motion.span>
            </AnimatePresence>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {feed?.synced_at && (
              <span className="hidden font-mono-k text-[11px] text-muted-foreground sm:inline" data-testid="home-ambient-status-sync">
                Synced {relTime(feed.synced_at)}
              </span>
            )}
            {!connected ? (
              <Button size="sm" variant="secondary" className="h-7 gap-1.5 text-xs" onClick={() => navigate("/accounts")} data-testid="home-status-connect">
                <Link2 size={13} /> Connect Google
              </Button>
            ) : push.supported && !push.subscribed ? (
              <Button size="sm" variant="secondary" className="h-7 gap-1.5 text-xs" onClick={enableAlerts} data-testid="home-status-enable-alerts">
                <BellRing size={13} /> Enable alerts
              </Button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Hero: presence + greeting + composer */}
      <motion.div className="glass rounded-2xl p-6 md:p-7" data-testid="home-hero"
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}>
        <div className="flex flex-col items-center gap-5 text-center md:flex-row md:items-start md:text-left">
          <div className="relative shrink-0">
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-[220px] w-[220px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60"
              style={{ background: "radial-gradient(circle, rgba(45,212,191,0.18), transparent 60%)" }} />
            <KaelraOrb size={132} state={orbState} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-center gap-2 md:justify-between">
              <div className="kaelra-kicker flex items-center gap-1.5"><Cpu size={12} /> Kaelra · present</div>
              <Button size="icon" variant={muted ? "ghost" : "secondary"} className="h-9 w-9"
                onClick={toggleMute} data-testid="kaelra-mute-toggle"
                aria-label={muted ? "Unmute Kaelra" : "Mute Kaelra"} aria-pressed={!muted}
                title={muted ? "Kaelra is muted" : "Kaelra speaks"}>
                {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </Button>
            </div>
            <p className="mt-2 whitespace-pre-line font-heading text-lg leading-relaxed md:text-xl" data-testid="kaelra-greeting">
              {greeting}
            </p>
            {muted && (
              <p className="mt-1.5 flex items-center justify-center gap-1.5 text-xs text-muted-foreground md:justify-start">
                <VolumeX size={12} className="text-[hsl(var(--accent))]" /> You're muted — I'll write instead of speak.
              </p>
            )}
          </div>
        </div>

        {/* Conversation composer */}
        <div className="mt-5" data-testid="home-composer">
          <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/5 p-2 focus-within:shadow-[var(--kaelra-focus)]">
            <Button size="icon" variant="ghost" className="shrink-0" onClick={onMic} data-testid="home-composer-listen-button"
              aria-label="Talk to Kaelra" aria-pressed={voice.listening}>
              <Mic size={18} className={voice.listening ? "text-[hsl(var(--primary))]" : ""} />
            </Button>
            <Textarea value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }}
              rows={1} placeholder="Tell me what you want done. I'll handle the rest."
              className="max-h-32 min-h-[44px] flex-1 resize-none border-0 bg-transparent focus-visible:ring-0"
              data-testid="home-composer-textarea" />
            {speaking && (
              <Button size="icon" variant="ghost" className="shrink-0" onClick={() => voice.stopSpeaking()} data-testid="home-composer-stop-button" aria-label="Stop speaking">
                <Square size={16} />
              </Button>
            )}
            <Button size="icon" className="shrink-0 rounded-xl" disabled={!input.trim()} onClick={() => ask()} data-testid="home-composer-send-button" aria-label="Send">
              <Send size={17} />
            </Button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {QUICK_INTENTS.map((s, i) => (
              <button key={s} onClick={() => ask(s)} data-testid={`home-composer-intent-${i}`}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground">
                {s}
              </button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Two-column intelligence */}
      <div className="mt-5 grid gap-5 lg:grid-cols-12">
        {/* Proactive feed */}
        <div className="lg:col-span-7" data-testid="home-proactive-feed">
          <SectionTitle kicker="Right now" title="Priority feed" icon={Activity}
            action={items.length > 0 ? (
              <Tabs value={tab} onValueChange={setTab}>
                <TabsList className="bg-white/5" data-testid="home-feed-tabs">
                  {FEED_TABS.map((t) => <TabsTrigger key={t.value} value={t.value} className="text-xs">{t.label}</TabsTrigger>)}
                </TabsList>
              </Tabs>
            ) : null} />
          {items.length === 0 ? (
            <div className="glass rounded-2xl p-8 text-center" data-testid="home-feed-empty">
              <KaelraOrb size={56} state="idle" className="mx-auto" />
              <p className="mt-3 font-heading">Nothing urgent right now.</p>
              <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
                Connect your Google and I'll start learning your patterns — the emails, meetings and files that matter — and surface them here.
              </p>
              <Button variant="secondary" className="mt-4 gap-1.5" onClick={() => navigate("/accounts")} data-testid="home-empty-connect-google">
                <Sparkles size={15} /> Connect Google
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.length === 0 && (
                <p className="px-1 py-6 text-center text-sm text-muted-foreground">Nothing in this view right now.</p>
              )}
              {filtered.map((item, idx) => {
                const Icon = KIND_ICON[item.kind] || Bell;
                return (
                  <button key={item.id} onClick={() => openItem(item)} data-testid={`home-feed-item-${idx}`}
                    className="group flex w-full items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-3.5 text-left transition-colors hover:bg-white/10 focus-visible:shadow-[var(--kaelra-focus)] min-h-[44px]">
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

        {/* What I've learned */}
        <div className="lg:col-span-5" data-testid="home-learned-stream">
          <SectionTitle kicker="Continuous memory" title="What I've learned" icon={Brain}
            action={<button onClick={() => navigate("/memory")} className="text-xs text-muted-foreground transition-colors hover:text-foreground" data-testid="home-learned-view-all">View memory</button>} />
          <div className="glass rounded-2xl p-4 md:p-5">
            {learned.length === 0 ? (
              <div className="py-6 text-center">
                <p className="text-sm text-muted-foreground">
                  I learn continuously from what you connect. The moment you link Google, I'll start remembering the people, deadlines and documents that matter — automatically.
                </p>
              </div>
            ) : (
              <ol className="relative space-y-3 before:absolute before:left-[5px] before:top-1 before:h-[calc(100%-0.5rem)] before:w-px before:bg-white/10">
                {learned.map((m, idx) => {
                  const SrcIcon = SOURCE_ICON[m.source] || Brain;
                  return (
                    <li key={m.id} className="relative pl-6" data-testid={`home-learned-item-${idx}`}>
                      <span className={`absolute left-0 top-1.5 h-[11px] w-[11px] rounded-full border-2 border-[hsl(var(--background))] ${m.important ? "bg-[hsl(var(--accent))]" : "bg-[hsl(var(--primary))]"}`} />
                      <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                        <div className="text-sm leading-snug">{m.content}</div>
                        <div className="mt-1.5 flex items-center gap-2 font-mono-k text-[11px] text-muted-foreground">
                          <SrcIcon size={11} className="text-[hsl(var(--primary))]" data-testid={`home-learned-item-${idx}-source`} />
                          <span>{m.source || "learned"}</span>
                          <span aria-hidden>·</span>
                          <span>{relTime(m.created_at)}</span>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
        </div>
      </div>

      <KaelraSpeaks item={selected} muted={muted} voice={voice} onClose={closeItem} />
    </div>
  );
}
