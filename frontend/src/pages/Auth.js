import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { KaelraOrb } from "../components/KaelraOrb";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Sparkles, ShieldCheck, Zap } from "lucide-react";

export default function Auth() {
  const { login, signup, demoLogin } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      let user;
      if (mode === "signin") user = await login(email, password);
      else user = await signup(email, password, name);
      toast.success(mode === "signin" ? "Welcome back." : "Welcome to Kaelra.");
      navigate(user.onboarded ? "/" : "/onboarding");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const doDemo = async () => {
    setBusy(true);
    try {
      const user = await demoLogin();
      toast.success("Signed in as Hetul (demo).");
      navigate(user.onboarded ? "/" : "/onboarding");
    } catch (err) {
      toast.error("Demo unavailable right now.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="kaelra-app-bg min-h-screen w-full grid lg:grid-cols-2">
      {/* Left: form */}
      <div className="flex items-center justify-center px-5 py-10">
        <div className="w-full max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <KaelraOrb size={48} />
            <div>
              <div className="font-heading text-2xl leading-none">Kaelra</div>
              <div className="kaelra-kicker mt-1">Personal AI Operator</div>
            </div>
          </div>

          <h1 className="font-heading text-3xl md:text-4xl mb-2">
            {mode === "signin" ? "Welcome back." : "Meet your operator."}
          </h1>
          <p className="text-muted-foreground mb-6">
            She knows what matters today and gets it ready before you ask.
          </p>

          <div className="glass rounded-2xl p-5">
            <div className="mb-4 grid grid-cols-2 gap-1 rounded-full bg-white/5 p-1">
              {["signin", "signup"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  data-testid={`auth-tab-${m}`}
                  className={`rounded-full py-2 text-sm transition-colors ${
                    mode === m ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "text-muted-foreground"
                  }`}
                >
                  {m === "signin" ? "Sign in" : "Create account"}
                </button>
              ))}
            </div>

            <form onSubmit={submit} className="space-y-3">
              {mode === "signup" && (
                <div>
                  <Label htmlFor="name">Your name</Label>
                  <Input id="name" data-testid="auth-name-input" value={name} onChange={(e) => setName(e.target.value)}
                    placeholder="Hetul" className="mt-1 bg-white/5 border-white/10" />
                </div>
              )}
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" required data-testid="auth-email-input" value={email}
                  onChange={(e) => setEmail(e.target.value)} placeholder="you@email.com"
                  className="mt-1 bg-white/5 border-white/10" />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" required data-testid="auth-password-input" value={password}
                  onChange={(e) => setPassword(e.target.value)} placeholder="••••••••"
                  className="mt-1 bg-white/5 border-white/10" />
              </div>
              <Button type="submit" disabled={busy} data-testid="auth-submit-button" className="w-full h-11">
                {busy ? "One moment…" : mode === "signin" ? "Sign in" : "Create account"}
              </Button>
            </form>

            <div className="my-4 flex items-center gap-3 text-xs text-muted-foreground">
              <div className="h-px flex-1 bg-white/10" /> or <div className="h-px flex-1 bg-white/10" />
            </div>

            <Button onClick={doDemo} disabled={busy} variant="secondary" data-testid="auth-demo-login-button"
              className="w-full h-11 gap-2">
              <Sparkles size={16} /> Explore the demo (Hetul)
            </Button>
          </div>
        </div>
      </div>

      {/* Right: ambient presence */}
      <div className="relative hidden lg:flex items-center justify-center overflow-hidden border-l border-white/10">
        <div className="absolute inset-0 opacity-60" style={{
          backgroundImage:
            "radial-gradient(700px circle at 60% 30%, rgba(45,212,191,0.18), transparent 60%), radial-gradient(600px circle at 30% 80%, rgba(56,189,248,0.16), transparent 60%)",
        }} />
        <div className="relative z-10 max-w-md px-10 text-center">
          <KaelraOrb size={200} state="idle" className="mb-8 mx-auto" />
          <p className="font-heading text-2xl leading-snug mb-6">
            “Good morning, Hetul. You work at 2 PM, so leave by 1:31. I drafted a reply
            and saved 5 job matches — want those first?”
          </p>
          <div className="flex items-center justify-center gap-5 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5"><ShieldCheck size={14} /> Approval-first</span>
            <span className="inline-flex items-center gap-1.5"><Zap size={14} /> Synced everywhere</span>
            <span className="inline-flex items-center gap-1.5"><Sparkles size={14} /> Always ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
