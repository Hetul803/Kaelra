import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { KaelraOrb } from "../components/KaelraOrb";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Progress } from "../components/ui/progress";
import {
  Calendar, Mail, FolderOpen, MapPin, Bell, Plus, X, Check, ArrowRight, ArrowLeft,
} from "lucide-react";

const TONES = [
  { id: "calm", label: "Calm", desc: "Grounding & unhurried" },
  { id: "friendly", label: "Friendly", desc: "Warm & personal" },
  { id: "direct", label: "Direct", desc: "Concise, no fluff" },
  { id: "energetic", label: "Energetic", desc: "Upbeat & motivating" },
];
const INTEREST_OPTS = ["AI", "startups", "backend engineering", "design", "finance", "health", "sports", "world news", "immigration"];
const AREA_OPTS = ["School", "Career", "Immigration", "Startup", "Family", "Finances", "Health", "Side projects"];
const FUTURE = [
  { icon: Calendar, name: "Google Calendar" },
  { icon: Mail, name: "Gmail" },
  { icon: FolderOpen, name: "Google Drive" },
  { icon: MapPin, name: "Maps / Commute" },
  { icon: Bell, name: "Notifications" },
];

function Chips({ options, value, onToggle, testid }) {
  return (
    <div className="flex flex-wrap gap-2" data-testid={testid}>
      {options.map((o) => {
        const active = value.includes(o);
        return (
          <button key={o} type="button" onClick={() => onToggle(o)}
            className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
              active ? "border-[hsl(var(--primary))] bg-[rgba(45,212,191,0.15)] text-foreground"
                     : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"}`}>
            {active && <Check size={13} className="mr-1 inline" />}{o}
          </button>
        );
      })}
    </div>
  );
}

export default function Onboarding() {
  const { user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    name: user?.name || "",
    call_me: user?.name || "",
    routine: "",
    goals: [],
    interests: ["AI", "startups"],
    life_areas: ["Career"],
    tone: "friendly",
    notifications_enabled: true,
    device_sync: true,
    proactive_briefing: true,
  });
  const [goalInput, setGoalInput] = useState("");
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggle = (k, v) => setForm((f) => ({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] }));

  const steps = useMemo(() => ([
    {
      title: "Let’s get acquainted",
      hint: "Kaelra will speak to you personally.",
      valid: form.name.trim() && form.call_me.trim(),
      body: (
        <div className="space-y-4">
          <div><Label>Your name</Label>
            <Input data-testid="onboarding-name" value={form.name} onChange={(e) => set("name", e.target.value)}
              placeholder="Hetul" className="mt-1 bg-white/5 border-white/10" /></div>
          <div><Label>What should Kaelra call you?</Label>
            <Input data-testid="onboarding-callme" value={form.call_me} onChange={(e) => set("call_me", e.target.value)}
              placeholder="Hetul" className="mt-1 bg-white/5 border-white/10" /></div>
        </div>
      ),
    },
    {
      title: "Your work & class routine",
      hint: "This helps Kaelra plan your day and leave-times.",
      valid: true,
      body: (
        <Textarea data-testid="onboarding-routine" value={form.routine} onChange={(e) => set("routine", e.target.value)}
          rows={5} className="bg-white/5 border-white/10"
          placeholder="e.g. CS student, classes Mon/Wed 11am, work shifts most afternoons at 2pm, building my startup on the side." />
      ),
    },
    {
      title: "What are you working toward?",
      hint: "Add a few goals Kaelra should help you move forward.",
      valid: true,
      body: (
        <div className="space-y-3">
          <div className="flex gap-2">
            <Input data-testid="onboarding-goal-input" value={goalInput} onChange={(e) => setGoalInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); if (goalInput.trim()) { set("goals", [...form.goals, goalInput.trim()]); setGoalInput(""); } } }}
              placeholder="Land a backend internship" className="bg-white/5 border-white/10" />
            <Button type="button" variant="secondary" data-testid="onboarding-goal-add"
              onClick={() => { if (goalInput.trim()) { set("goals", [...form.goals, goalInput.trim()]); setGoalInput(""); } }}>
              <Plus size={16} />
            </Button>
          </div>
          <div className="flex flex-col gap-2">
            {form.goals.map((g, i) => (
              <div key={i} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm">
                <span className="flex-1">{g}</span>
                <button onClick={() => set("goals", form.goals.filter((_, j) => j !== i))}><X size={14} /></button>
              </div>
            ))}
            {form.goals.length === 0 && <p className="text-sm text-muted-foreground">No goals yet — you can add these later too.</p>}
          </div>
        </div>
      ),
    },
    {
      title: "Interests & areas to watch",
      hint: "Kaelra tailors your news briefing and what she monitors.",
      valid: true,
      body: (
        <div className="space-y-5">
          <div><Label className="mb-2 block">News interests</Label>
            <Chips testid="onboarding-interests" options={INTEREST_OPTS} value={form.interests} onToggle={(v) => toggle("interests", v)} /></div>
          <div><Label className="mb-2 block">Life areas to track</Label>
            <Chips testid="onboarding-areas" options={AREA_OPTS} value={form.life_areas} onToggle={(v) => toggle("life_areas", v)} /></div>
        </div>
      ),
    },
    {
      title: "How should Kaelra feel?",
      hint: "Pick a tone and how proactive she should be.",
      valid: true,
      body: (
        <div className="space-y-5">
          <div className="grid grid-cols-2 gap-2" data-testid="onboarding-tone">
            {TONES.map((t) => (
              <button key={t.id} type="button" onClick={() => set("tone", t.id)}
                className={`rounded-xl border p-3 text-left transition-colors ${
                  form.tone === t.id ? "border-[hsl(var(--primary))] bg-[rgba(45,212,191,0.12)]" : "border-white/10 bg-white/5"}`}>
                <div className="font-heading">{t.label}</div>
                <div className="text-xs text-muted-foreground">{t.desc}</div>
              </button>
            ))}
          </div>
          {[
            ["proactive_briefing", "Brief me every morning", "Kaelra prepares your day before you ask."],
            ["notifications_enabled", "Send me reminders", "Leave-times, deadlines and important changes."],
            ["device_sync", "Keep my phone & laptop in sync", "Continue seamlessly across devices."],
          ].map(([k, label, desc]) => (
            <div key={k} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <div><div className="text-sm">{label}</div><div className="text-xs text-muted-foreground">{desc}</div></div>
              <Switch checked={form[k]} onCheckedChange={(v) => set(k, v)} data-testid={`onboarding-switch-${k}`} />
            </div>
          ))}
        </div>
      ),
    },
    {
      title: "Connect your world (optional)",
      hint: "Kaelra works with realistic demo data now — connect these for real later.",
      valid: true,
      body: (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {FUTURE.map((c) => (
            <div key={c.name} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]"><c.icon size={16} /></span>
              <div className="flex-1"><div className="text-sm">{c.name}</div>
                <div className="text-xs text-muted-foreground font-mono-k">Demo connected</div></div>
              <Check size={16} className="text-[hsl(var(--primary))]" />
            </div>
          ))}
        </div>
      ),
    },
  ]), [form, goalInput]);

  const current = steps[step];
  const pct = Math.round(((step + 1) / steps.length) * 100);

  const next = async () => {
    if (!current.valid) { toast.error("Please complete this step."); return; }
    if (step < steps.length - 1) { setStep(step + 1); return; }
    setBusy(true);
    try {
      await api.post("/onboarding", form);
      await refreshProfile();
      toast.success("Kaelra is ready for you.");
      navigate("/");
    } catch (e) {
      toast.error("Could not save onboarding.");
    } finally { setBusy(false); }
  };

  return (
    <div className="kaelra-app-bg min-h-screen flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-6 flex items-center gap-3">
          <KaelraOrb size={44} state="thinking" />
          <div className="flex-1">
            <div className="kaelra-kicker">Setting up · {step + 1} of {steps.length}</div>
            <Progress value={pct} className="mt-2 h-1.5 bg-white/10" />
          </div>
        </div>

        <div className="glass rounded-2xl p-6 kaelra-fade-up" key={step}>
          <h2 className="font-heading text-2xl" data-testid="onboarding-step-title">{current.title}</h2>
          <p className="text-sm text-muted-foreground mt-1 mb-5">{current.hint}</p>
          {current.body}
        </div>

        <div className="mt-5 flex items-center justify-between">
          <Button variant="ghost" data-testid="onboarding-back-button" disabled={step === 0 || busy}
            onClick={() => setStep(Math.max(0, step - 1))} className="gap-1">
            <ArrowLeft size={16} /> Back
          </Button>
          <Button data-testid="onboarding-next-button" onClick={next} disabled={busy} className="gap-1 px-6">
            {step === steps.length - 1 ? (busy ? "Preparing…" : "Enter Kaelra") : "Continue"}
            {step === steps.length - 1 ? <Check size={16} /> : <ArrowRight size={16} />}
          </Button>
        </div>
      </div>
    </div>
  );
}
