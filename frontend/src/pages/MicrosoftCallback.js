import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { KaelraOrb } from "../components/KaelraOrb";

// OAuth redirect target for Microsoft (window.location.origin + "/auth/microsoft").
export default function MicrosoftCallback() {
  const navigate = useNavigate();
  const [msg, setMsg] = useState("Securely connecting your Microsoft account…");
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
      toast.error("Microsoft connection cancelled.");
      navigate("/accounts", { replace: true });
      return;
    }
    const redirect_uri = window.location.origin + "/auth/microsoft";
    (async () => {
      try {
        const { data } = await api.post("/oauth/microsoft/callback", { code, redirect_uri, state });
        toast.success(`Connected ${data.email || "your Microsoft account"}.`);
      } catch (e) {
        toast.error(e?.response?.data?.detail || "Microsoft connection failed.");
      } finally {
        window.history.replaceState({}, "", "/auth/microsoft");
        navigate("/accounts", { replace: true });
      }
    })();
  }, [navigate]);

  return (
    <div className="kaelra-app-bg min-h-screen flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-md glass rounded-2xl p-8" data-testid="microsoft-callback">
        <div className="flex flex-col items-center text-center gap-4">
          <KaelraOrb size={96} state="thinking" />
          <p className="font-mono-k text-sm text-muted-foreground">{msg}</p>
        </div>
      </div>
    </div>
  );
}
