import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("kaelra_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("kaelra_token");
      if (!window.location.pathname.startsWith("/auth")) {
        window.location.href = "/auth";
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Stream a chat message via SSE (fetch + ReadableStream so we can send the
 * Authorization header, which EventSource cannot do).
 * onEvent receives parsed event objects: {type:'delta'|'session'|'actions'|'done'|'error', ...}
 */
export async function streamChat({ message, sessionId, onEvent, signal }) {
  const token = localStorage.getItem("kaelra_token");
  const res = await fetch(`${API}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, session_id: sessionId || null }),
    signal,
  });
  if (!res.ok || !res.body) {
    onEvent({ type: "error", message: "Kaelra could not respond right now." });
    onEvent({ type: "done" });
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() || "";
      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line.startsWith("data:")) continue;
        const json = line.slice(5).trim();
        if (!json) continue;
        try {
          onEvent(JSON.parse(json));
        } catch (e) {
          /* ignore partial */
        }
      }
    }
  } catch (e) {
    if (e?.name === "AbortError") return; // stream cancelled by caller
    onEvent({ type: "error", message: "Connection interrupted." });
    onEvent({ type: "done" });
  }
}
