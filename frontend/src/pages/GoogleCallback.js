import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { ContextBuilder } from "../components/ContextBuilder";
import { KaelraOrb } from "../components/KaelraOrb";

/**
 * OAuth redirect target (window.location.origin + "/auth/google").
 * Exchanges the Google authorization code for tokens, then runs the
 * Context Builder before sending the user into Kaelra.
 */
export default function GoogleCallback() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState("connecting"); // connecting | building
  const ranRef = useRef(false);

  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    const token = localStorage.getItem("kaelra_token");
    if (!token) { navigate("/auth", { replace: true }); return; }

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const err = params.get("error");

    if (err || !code) {
      toast.error(err === "access_denied" ? "Google connection cancelled." : "Google connection failed.");
      navigate("/accounts", { replace: true });
      return;
    }

    const redirect_uri = window.location.origin + "/auth/google";
    (async () => {
      try {
        const { data } = await api.post("/oauth/google/callback", { code, redirect_uri, state });
        toast.success(`Connected ${data.email || "your Google account"}.`);
        window.history.replaceState({}, "", "/auth/google");
        setPhase("building");
      } catch (e) {
        toast.error(e?.response?.data?.detail || "Google connection failed.");
        navigate("/accounts", { replace: true });
      }
    })();
  }, [navigate]);

  return (
    <div className="kaelra-app-bg min-h-screen flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-md glass rounded-2xl p-8" data-testid="google-callback">
        {phase === "connecting" ? (
          <div className="flex flex-col items-center text-center gap-4">
            <KaelraOrb size={96} state="thinking" />
            <p className="font-mono-k text-sm text-muted-foreground">Securely connecting your Google account…</p>
          </div>
        ) : (
          <ContextBuilder onDone={() => navigate("/", { replace: true })} />
        )}
      </div>
    </div>
  );
}
