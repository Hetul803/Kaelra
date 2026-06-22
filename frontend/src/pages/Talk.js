import React, { useEffect, useRef, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api, streamChat } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { KaelraOrb, ORB_STATUS } from "../components/KaelraOrb";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import { ScrollArea } from "../components/ui/scroll-area";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "../components/ui/sheet";
import { Mic, Send, History, Plus, Trash2, MessageCircle } from "lucide-react";

const SUGGESTIONS = [
  "What’s my day like?",
  "When should I leave?",
  "Do I have any important emails?",
  "What assignments do I have?",
  "Draft a reply to Prof. Adams.",
  "What did I miss while I was asleep?",
];

export default function Talk() {
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [orbState, setOrbState] = useState("idle");
  const [streaming, setStreaming] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const scrollRef = useRef(null);
  const startedRef = useRef(false);
  const streamTokenRef = useRef(0);
  const abortRef = useRef(null);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (el) el.scrollTop = el.scrollHeight;
    });
  };

  const loadSessions = useCallback(async () => {
    try {
      const { data } = await api.get("/chat/sessions");
      setSessions(data);
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => { loadSessions(); }, [loadSessions]);
  useEffect(scrollToBottom, [messages]);

  const send = useCallback(async (text) => {
    const message = (text ?? input).trim();
    if (!message || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setStreaming(true);
    setOrbState("thinking");

    const myToken = ++streamTokenRef.current;
    const controller = new AbortController();
    abortRef.current = controller;
    let firstDelta = true;
    await streamChat({
      message,
      sessionId,
      signal: controller.signal,
      onEvent: (ev) => {
        if (streamTokenRef.current !== myToken) return; // stale stream (new chat started)
        if (ev.type === "session") {
          setSessionId(ev.session_id);
        } else if (ev.type === "delta") {
          if (firstDelta) { setOrbState("speaking"); firstDelta = false; }
          setMessages((m) => {
            if (m.length === 0) return m;
            const copy = [...m];
            const last = copy[copy.length - 1];
            if (!last || last.role !== "assistant") return m;
            copy[copy.length - 1] = { role: "assistant", content: last.content + ev.content };
            return copy;
          });
          scrollToBottom();
        } else if (ev.type === "actions") {
          if (ev.actions && ev.actions.length > 0) {
            toast.success(`Kaelra prepared ${ev.actions.length} action${ev.actions.length > 1 ? "s" : ""} for your approval.`);
            triggerKaelraRefresh();
          }
        } else if (ev.type === "error") {
          toast.error(ev.message || "Kaelra hit a snag.");
        } else if (ev.type === "done") {
          setStreaming(false);
          setOrbState("idle");
          loadSessions();
        }
      },
    });
  }, [input, sessionId, streaming, loadSessions]);

  // Auto-send the command-bar message passed via navigation
  useEffect(() => {
    const initial = location.state?.initialMessage;
    if (initial && !startedRef.current) {
      startedRef.current = true;
      navigate("/talk", { replace: true, state: {} });
      send(initial);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  const cancelStream = () => {
    streamTokenRef.current++;
    if (abortRef.current) { try { abortRef.current.abort(); } catch (e) { /* noop */ } abortRef.current = null; }
    setStreaming(false);
    setOrbState("idle");
  };

  const newChat = () => {
    cancelStream();
    setMessages([]);
    setSessionId(null);
    setHistoryOpen(false);
    startedRef.current = true;
  };

  const openSession = async (sid) => {
    cancelStream();
    try {
      const { data } = await api.get(`/chat/sessions/${sid}/messages`);
      setMessages(data.map((m) => ({ role: m.role, content: m.content })));
      setSessionId(sid);
      setHistoryOpen(false);
      startedRef.current = true;
    } catch (e) { toast.error("Couldn't load that conversation."); }
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    await api.delete(`/chat/sessions/${sid}`);
    if (sid === sessionId) newChat();
    loadSessions();
  };

  const onVoice = () => {
    setOrbState("listening");
    toast("Kaelra is voice-ready — live voice is coming soon.", { description: "She’ll speak and listen here." });
    setTimeout(() => setOrbState((s) => (s === "listening" ? "idle" : s)), 1600);
  };

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-150px)] max-w-3xl flex-col">
      {/* Presence header */}
      <div className="flex items-center justify-between gap-3 pb-3">
        <div className="flex items-center gap-3">
          <KaelraOrb size={48} state={orbState} />
          <div>
            <div className="font-heading text-lg leading-none">Kaelra</div>
            <div className="text-xs text-muted-foreground font-mono-k">{ORB_STATUS[orbState]}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" className="gap-1.5" onClick={newChat} data-testid="talk-new-chat">
            <Plus size={15} /> New
          </Button>
          <Sheet open={historyOpen} onOpenChange={setHistoryOpen}>
            <SheetTrigger asChild>
              <Button size="sm" variant="ghost" className="gap-1.5" data-testid="talk-history-button"><History size={15} /> History</Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[320px] border-white/10 bg-[rgba(15,22,32,0.96)] backdrop-blur-xl">
              <SheetHeader><SheetTitle className="font-heading">Conversations</SheetTitle></SheetHeader>
              <div className="mt-4 flex flex-col gap-2">
                {sessions.length === 0 && <p className="text-sm text-muted-foreground">No conversations yet.</p>}
                {sessions.map((s) => (
                  <button key={s.id} onClick={() => openSession(s.id)}
                    className="group flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left hover:bg-white/10">
                    <MessageCircle size={15} className="text-[hsl(var(--primary))] shrink-0" />
                    <span className="flex-1 truncate text-sm">{s.title}</span>
                    <button onClick={(e) => deleteSession(s.id, e)} className="opacity-0 group-hover:opacity-100"><Trash2 size={14} /></button>
                  </button>
                ))}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto rounded-2xl" data-testid="talk-message-list">
        {empty ? (
          <div className="flex h-full flex-col items-center justify-center px-4 text-center">
            <KaelraOrb size={120} state="idle" className="mb-5" />
            <h2 className="font-heading text-2xl">How can I help you move through today?</h2>
            <p className="mt-1 text-sm text-muted-foreground">I have your schedule, emails, goals and files ready.</p>
            <div className="mt-5 flex max-w-lg flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} data-testid="talk-suggestion-chip"
                  className="rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-white/10 hover:text-foreground">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 py-2">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "assistant" && <KaelraOrb size={30} state="idle" className="mt-1 shrink-0" />}
                <div className={`max-w-[78%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed kaelra-fade-up ${
                  m.role === "user"
                    ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
                    : "glass text-foreground/95"
                }`}>
                  {m.content === "" && streaming ? (
                    <span className="font-mono-k text-sm text-muted-foreground">Kaelra is thinking…</span>
                  ) : (
                    <span className="whitespace-pre-line">{m.content}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="pt-3">
        <div className="glass flex items-end gap-2 rounded-2xl p-2 focus-within:shadow-[var(--kaelra-focus)]">
          <Button size="icon" variant="ghost" onClick={onVoice} data-testid="talk-voice-button" aria-label="Voice"
            className={`shrink-0 ${orbState === "listening" ? "text-[hsl(var(--primary))]" : ""}`}>
            <Mic size={18} />
          </Button>
          <Textarea
            data-testid="talk-composer-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={1}
            placeholder="Talk to Kaelra…"
            className="max-h-32 min-h-[40px] flex-1 resize-none border-0 bg-transparent focus-visible:ring-0"
          />
          <Button size="icon" disabled={streaming || !input.trim()} onClick={() => send()} data-testid="talk-send-button"
            className="shrink-0 rounded-xl" aria-label="Send">
            <Send size={17} />
          </Button>
        </div>
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Kaelra is an AI operator. She prepares actions and asks before doing anything sensitive.
        </p>
      </div>
    </div>
  );
}
