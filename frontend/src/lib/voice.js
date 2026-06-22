import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

/**
 * Voice layer for Kaelra.
 * - TTS: tries backend ElevenLabs (premium); falls back to browser speechSynthesis.
 * - STT: browser Web Speech API (SpeechRecognition).
 * Everything degrades gracefully when unsupported.
 */
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
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
    setListening(true);
    return true;
  }, [sttSupported]);

  const stopListening = useCallback(() => {
    try { recognitionRef.current?.stop(); } catch (e) { /* noop */ }
    setListening(false);
  }, []);

  return { provider, speaking, listening, sttSupported, speak, stopSpeaking, startListening, stopListening };
}
