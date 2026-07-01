import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

/**
 * Voice layer for Kaelra.
 * - TTS: tries backend ElevenLabs (premium); falls back to browser speechSynthesis.
 * - STT: browser Web Speech API (SpeechRecognition).
 * Everything degrades gracefully when unsupported.
 */
let _lastSpeak = { text: "", ts: 0 };

/**
 * Free, module-level browser TTS. Used for Kaelra's short "Entity" confirmations
 * ("Here's your calendar.", "What's next?") so we NEVER spend premium ElevenLabs
 * credits on canned navigation chatter. De-duped like the premium path.
 */
export function speakBrowser(text) {
  if (!text || typeof window === "undefined" || !window.speechSynthesis) return;
  const now = Date.now();
  if (text === _lastSpeak.text && now - _lastSpeak.ts < 4000) return;
  _lastSpeak = { text, ts: now };
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    u.pitch = 1.0;
    window.speechSynthesis.speak(u);
  } catch (e) {
    /* noop */
  }
}

export function useVoice() {
  const [provider, setProvider] = useState("browser");
  const [speaking, setSpeaking] = useState(false);
  const [listening, setListening] = useState(false);
  const audioRef = useRef(null);
  const recognitionRef = useRef(null);

  const sttSupported =
    typeof window !== "undefined" &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  useEffect(() => {
    api.get("/voice/status").then(({ data }) => setProvider(data.provider)).catch(() => {});
  }, []);

  const stopSpeaking = useCallback(() => {
    try {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    } catch (e) { /* noop */ }
    setSpeaking(false);
  }, []);

  const speak = useCallback(async (text) => {
    if (!text) return;
    // De-dupe: ignore an identical narration fired within 4s (prevents the
    // "speaks twice back to back" issue from remounts / fallback paths).
    const now = Date.now();
    if (text === _lastSpeak.text && now - _lastSpeak.ts < 4000) return;
    _lastSpeak = { text, ts: now };
    stopSpeaking();
    setSpeaking(true);
    // Try premium TTS via backend
    try {
      const { data } = await api.post("/voice/tts", { text });
      if (data.audio) {
        const audio = new Audio(data.audio);
        audioRef.current = audio;
        audio.onended = () => setSpeaking(false);
        audio.onerror = () => setSpeaking(false);
        await audio.play();
        return;
      }
    } catch (e) { /* fall through to browser */ }
    // Browser fallback
    try {
      if (window.speechSynthesis) {
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0; u.pitch = 1.0;
        u.onend = () => setSpeaking(false);
        window.speechSynthesis.speak(u);
      } else {
        setSpeaking(false);
      }
    } catch (e) { setSpeaking(false); }
  }, [stopSpeaking]);

  const startListening = useCallback((onResult) => {
    if (!sttSupported) return false;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      onResult?.(transcript);
    };
    rec.onend = () => {
      setListening(false);
      // Release the mic so the global wake-word presence can resume.
      try { window.dispatchEvent(new Event("kaelra-stt-end")); } catch (x) { /* noop */ }
    };
    rec.onerror = () => {
      setListening(false);
      try { window.dispatchEvent(new Event("kaelra-stt-end")); } catch (x) { /* noop */ }
    };
    recognitionRef.current = rec;
    // Ask the global wake-word presence to pause while we own the mic.
    try { window.dispatchEvent(new Event("kaelra-stt-start")); } catch (x) { /* noop */ }
    rec.start();
    setListening(true);
    return true;
  }, [sttSupported]);

  const stopListening = useCallback(() => {
    try { recognitionRef.current?.stop(); } catch (e) { /* noop */ }
    setListening(false);
    try { window.dispatchEvent(new Event("kaelra-stt-end")); } catch (e) { /* noop */ }
  }, []);

  // Free browser-only narration for short confirmations (no premium spend).
  const speakLocal = useCallback((text) => {
    if (!text) return;
    stopSpeaking();
    setSpeaking(true);
    try {
      if (window.speechSynthesis) {
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1.0; u.pitch = 1.0;
        u.onend = () => setSpeaking(false);
        u.onerror = () => setSpeaking(false);
        window.speechSynthesis.speak(u);
      } else { setSpeaking(false); }
    } catch (e) { setSpeaking(false); }
  }, [stopSpeaking]);

  return { provider, speaking, listening, sttSupported, speak, speakLocal, stopSpeaking, startListening, stopListening };
}
