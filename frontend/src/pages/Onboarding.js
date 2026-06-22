import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { KaelraOrb } from "../components/KaelraOrb";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import {
  Calendar, Mail, FolderOpen, ShieldCheck, ArrowRight, Sparkles, Lock,
} from "lucide-react";

const LEARNS = [
  { icon: Calendar, label: "Calendar", note: "your schedule & leave-times" },
  { icon: Mail, label: "Gmail", note: "what's urgent, who needs a reply" },
  { icon: FolderOpen, label: "Drive", note: "resumes, forms, deadlines" },
];

export default function Onboarding() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [callMe, setCallMe] = useState(user?.name || "");
  const [busy, setBusy] = useState(false);

  const saveMinimal = async () => {
    const name = (user?.name || callMe || "there").trim();
    await api.post("/onboarding", { name, call_me: (callMe || name).trim() });
  };

  const connectGoogle = async () => {
    if (!callMe.trim()) { toast.error("Tell me what to call you first."); return; }
    setBusy(true);
    try {
      await saveMinimal();
      const redirect_uri = window.location.origin + "/auth/google";
      const { data } = await api.get("/oauth/google/url", { params: { redirect_uri } });
      window.location.href = data.url; // full-page redirect to Google consent
    } catch (e) {
      setBusy(false);
      if (e?.response?.status === 400) {
        toast.message("Google isn't configured yet — starting you on demo data.");
        await refreshProfile();
        navigate("/");
      } else {
        toast.error("Couldn't start the Google connection. Try again.");
      }
    }
  };

  const continueDemo = async () => {
    if (!callMe.trim()) { toast.error("Tell me what to call you first."); return; }
    setBusy(true);
    try {
      await saveMinimal();
      await refreshProfile();
      toast.success("You're in. Connect Google anytime so I can learn more.");
      navigate("/");
    } catch (e) {
      setBusy(false);
      toast.error("Couldn't continue. Try again.");
    }
  };

  return (
    <div className="kaelra-app-bg min-h-screen flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-lg">
        <div className="glass rounded-2xl p-7 kaelra-fade-up">
          <div className="flex flex-col items-center text-center">
            <KaelraOrb size={92} state="idle" />
            <h1 className="mt-5 font-heading text-2xl" data-testid="onboarding-step-title">Hi, I'm Kaelra.</h1>
            <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">
              Connect your Google and I'll learn what matters to you — your schedule, the people and
              deadlines that matter, what's urgent. You won't have to explain yourself.
            </p>
          </div>

          {/* What she'll learn */}
          <div className="mt-6 grid grid-cols-3 gap-2">
            {LEARNS.map(({ icon: Icon, label, note }) => (
              <div key={label} className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                <Icon size={18} className="mx-auto text-[hsl(var(--primary))]" />
                <div className="mt-1.5 text-sm">{label}</div>
                <div className="mt-0.5 text-[11px] leading-tight text-muted-foreground">{note}</div>
              </div>
            ))}
          </div>

          {/* Name */}
          <div className="mt-6">
            <Label className="mb-1 block">What should I call you?</Label>
            <Input data-testid="onboarding-callme" value={callMe} autoFocus
              onChange={(e) => setCallMe(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") connectGoogle(); }}
              placeholder="Hetul" className="bg-white/5 border-white/10" />
          </div>

          {/* Primary: connect google */}
          <Button className="mt-5 w-full gap-2" disabled={busy} onClick={connectGoogle} data-testid="onboarding-connect-google">
            <Sparkles size={16} /> {busy ? "Opening Google…" : "Connect Google & let Kaelra learn"}
            {!busy && <ArrowRight size={16} className="ml-auto" />}
          </Button>

          {/* Secondary: demo */}
          <Button variant="ghost" className="mt-2 w-full text-muted-foreground" disabled={busy}
            onClick={continueDemo} data-testid="onboarding-next-button">
            Explore with demo data first
          </Button>

          {/* Trust row */}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground">
            <span className="inline-flex items-center gap-1.5"><Lock size={12} className="text-[hsl(var(--primary))]" /> Read-only access</span>
            <span className="inline-flex items-center gap-1.5"><ShieldCheck size={12} className="text-[hsl(var(--primary))]" /> Approval before anything sends</span>
            <span className="inline-flex items-center gap-1.5"><Sparkles size={12} className="text-[hsl(var(--primary))]" /> You can disconnect anytime</span>
          </div>
        </div>

        <p className="mt-4 text-center text-[11px] text-muted-foreground">
          I only ever use the sources you connect. You stay in control in Settings → Privacy.
        </p>
      </div>
    </div>
  );
}
