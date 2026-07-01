import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { startTracking } from "../lib/location";
import { speakBrowser } from "../lib/voice";
import { interpretCommand, executeCommand } from "../lib/kaelraCommand";
import { Mic, MicOff } from "lucide-react";

// Global Kaelra presence — she's reachable and listening on every screen.
// "Hey Kaelra" wake-word via the browser SpeechRecognition API (Chrome-class
// browsers, while the app is open). Commands are resolved LOCALLY first (free,
// no LLM/premium-voice spend); only real reasoning is handed to /talk.
//
// Default ON per the Entity vision. Browsers require a user gesture before the
// mic can start, so if the initial start is blocked we arm it on the first tap.
const WAKE_KEY = "kaelra_wake"; // "0" = user turned it off; anything else = on

export function KaelraPresence() {
  const navigate = useNavigate();
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const recRef = useRef(null);
  const wantRef = useRef(false);
  const pausedRef = useRef(false); // paused because a page owns the mic (STT)

  // Opt-in location timeline resumes if the user enabled it previously.
  useEffect(() => { startTracking(); }, []);

  const startRec = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR || recRef.current) return true;
    try {
      const rec = new SR();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = "en-US";
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) handleTranscript(e.results[i][0].transcript);
        }
      };
      rec.onend = () => {
        recRef.current = null;
        setListening(false);
        if (wantRef.current && !pausedRef.current) {
          // Re-arm continuous listening after the browser auto-stops it.
          setTimeout(() => { if (wantRef.current && !pausedRef.current) startRec(); }, 300);
        }
      };
      rec.onerror = () => { /* transient; onend re-arms */ };
      recRef.current = rec;
      rec.start();
      setListening(true);
      return true;
    } catch (e) {
      recRef.current = null;
      return false; // needs a user gesture
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopRec = useCallback(() => {
    try { recRef.current && recRef.current.stop(); } catch (e) { /* noop */ }
    recRef.current = null;
    setListening(false);
  }, []);

  const handleTranscript = (text) => {
    const raw = (text || "").toString();
    const t = raw.toLowerCase();
    const idx = t.indexOf("kaelra");
    if (idx === -1) return; // only respond to her name
    const cmd = raw.slice(idx + "kaelra".length).replace(/^[,\s.!?]+/, "").trim();
    if (!cmd) { speakBrowser("I'm here. What would you like me to pull up?"); return; }

    const interpreted = interpretCommand(cmd);
    const handled = executeCommand({
      cmd: interpreted,
      navigate,
      speak: speakBrowser,
      stopSpeaking: () => { try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (e) { /* noop */ } },
    });
    if (!handled) {
      // Real reasoning -> full conversation (LLM).
      navigate("/talk", { state: { initialMessage: cmd } });
    }
  };

  const enable = useCallback((announce) => {
    wantRef.current = true;
    localStorage.setItem(WAKE_KEY, "1");
    const ok = startRec();
    if (!ok) {
      // Arm on the first user gesture (browser mic gesture requirement).
      const arm = () => {
        window.removeEventListener("pointerdown", arm);
        window.removeEventListener("keydown", arm);
        if (wantRef.current) startRec();
      };
      window.addEventListener("pointerdown", arm, { once: true });
      window.addEventListener("keydown", arm, { once: true });
    }
    if (announce) toast.success("Listening for \u201cHey Kaelra\u2026\u201d");
  }, [startRec]);

  const disable = useCallback((announce) => {
    wantRef.current = false;
    localStorage.setItem(WAKE_KEY, "0");
    stopRec();
    if (announce) toast.message("Wake word off.");
  }, [stopRec]);

  // Initial mount: default ON unless the user turned it off.
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    setSupported(true);
    if (localStorage.getItem(WAKE_KEY) !== "0") enable(false);
    return () => { wantRef.current = false; stopRec(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Yield the mic while a page-level STT session is active, then resume.
  useEffect(() => {
    const onAcquire = () => {
      if (!wantRef.current) return;
      pausedRef.current = true;
      stopRec();
    };
    const onRelease = () => {
      if (!wantRef.current) { pausedRef.current = false; return; }
      pausedRef.current = false;
      setTimeout(() => { if (wantRef.current && !pausedRef.current) startRec(); }, 400);
    };
    window.addEventListener("kaelra-stt-start", onAcquire);
    window.addEventListener("kaelra-stt-end", onRelease);
    return () => {
      window.removeEventListener("kaelra-stt-start", onAcquire);
      window.removeEventListener("kaelra-stt-end", onRelease);
    };
  }, [startRec, stopRec]);

  const toggle = () => {
    if (wantRef.current) disable(true);
    else enable(true);
  };

  if (!supported) return null;

  return (
    <button
      onClick={toggle}
      data-testid="kaelra-wakeword-toggle"
      aria-label={listening ? "Turn off Hey Kaelra" : "Turn on Hey Kaelra wake word"}
      aria-pressed={listening}
      title={listening ? "Listening for \u2018Hey Kaelra\u2026\u2019" : "Say \u2018Hey Kaelra\u2019 anywhere"}
      className={`fixed left-4 bottom-24 z-[9998] flex h-12 w-12 items-center justify-center rounded-full border shadow-lg backdrop-blur-md transition-colors lg:left-6 lg:bottom-6 ${
        listening
          ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/20 text-[hsl(var(--primary))]"
          : "border-white/10 bg-[rgba(15,22,32,0.9)] text-muted-foreground hover:text-foreground"
      }`}
    >
      {listening && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(var(--primary))] opacity-30" />
      )}
      {listening ? <Mic size={20} className="relative" /> : <MicOff size={20} className="relative" />}
    </button>
  );
}
