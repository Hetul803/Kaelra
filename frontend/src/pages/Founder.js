import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  AreaChart, Area, XAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Progress } from "../components/ui/progress";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Rocket, Plus, CheckCircle2, Circle, TrendingUp, Sparkles, PenLine, Megaphone, Target,
} from "lucide-react";

const STATUSES = ["todo", "in_progress", "done"];
const STATUS_LABEL = { todo: "To do", in_progress: "In progress", done: "Done" };
const PRIORITY_TONE = { high: "red", medium: "amber", low: "default" };

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
      <div className="font-heading text-xl">{value}</div>
      <div className="text-[11px] text-muted-foreground">{label}</div>
    </div>
  );
}

export default function Founder() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [taskTitle, setTaskTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/founder");
    setData(data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const addTask = async () => {
    if (!taskTitle.trim()) return;
    try {
      await api.post("/founder/tasks", { title: taskTitle.trim(), priority: "medium" });
      setTaskTitle("");
      await load();
    } catch (e) { toast.error("Couldn't add task."); }
  };

  const setTaskStatus = async (t, status) => {
    try { await api.post(`/founder/tasks/${t.id}/status`, { status }); await load(); }
    catch (e) { toast.error("Couldn't update task."); }
  };

  const toggleChecklist = async (c) => {
    try { await api.post(`/founder/checklist/${c.id}/toggle`); await load(); }
    catch (e) { toast.error("Couldn't update checklist."); }
  };

  const draftPost = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/founder/draft-post", { topic });
      setResult({ title: "LinkedIn launch post (draft)", body: data.post });
      toast.success("Post drafted — it only publishes after you approve it.");
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't draft a post."); }
    finally { setBusy(false); }
  };

  const summarizeMetrics = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/founder/summarize-metrics");
      setResult({ title: "Growth read", body: data.summary });
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't summarize metrics."); }
    finally { setBusy(false); }
  };

  if (loading) return <LoadingState label="Loading your workspace…" />;

  const project = data?.project || {};
  const tasks = data?.tasks || [];
  const checklist = data?.checklist || [];
  const metrics = data?.metrics || {};
  const series = metrics.series || [];
  const doneCount = checklist.filter((c) => c.done).length;
  const pct = checklist.length ? Math.round((doneCount / checklist.length) * 100) : 0;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="kaelra-kicker">Founder workspace</div>
          <h1 className="font-heading text-2xl">{project.name || "Workspace"}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{project.tagline}</p>
        </div>
        {project.stage && <StatusPill tone="teal">{project.stage}</StatusPill>}
      </div>

      <div className="grid gap-4 lg:grid-cols-12">
        {/* Metrics */}
        <GlassCard className="rounded-2xl p-4 lg:col-span-7" data-testid="founder-metrics">
          <SectionTitle kicker="This week" title="Traction" icon={TrendingUp}
            action={<Button size="sm" variant="ghost" className="gap-1 text-xs" disabled={busy} onClick={summarizeMetrics} data-testid="founder-summarize-metrics-button"><Sparkles size={13} /> Read</Button>} />
          <div className="grid grid-cols-4 gap-2">
            <Stat label="impressions" value={metrics.impressions ?? 0} />
            <Stat label="clicks" value={metrics.clicks ?? 0} />
            <Stat label="CTR %" value={metrics.ctr ?? 0} />
            <Stat label="signups" value={metrics.signups ?? 0} />
          </div>
          <div className="mt-3 h-[160px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series} margin={{ top: 6, right: 6, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="impGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2DD4BF" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="#2DD4BF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
                <XAxis dataKey="day" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "rgba(15,22,32,0.96)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, color: "#EAF0F7", fontSize: 12 }}
                  labelStyle={{ color: "#A9B4C2" }} cursor={{ stroke: "rgba(45,212,191,0.4)" }} />
                <Area type="monotone" dataKey="impressions" stroke="#2DD4BF" strokeWidth={2} fill="url(#impGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          {metrics.trend && <p className="mt-1 text-xs text-muted-foreground">{metrics.trend}</p>}
        </GlassCard>

        {/* Launch checklist */}
        <GlassCard className="rounded-2xl p-4 lg:col-span-5" data-testid="founder-checklist">
          <SectionTitle kicker={`${pct}% ready`} title="Launch checklist" icon={Target} />
          <Progress value={pct} className="mb-3 h-1.5 bg-white/10" />
          <div className="space-y-1.5">
            {checklist.map((c) => (
              <button key={c.id} onClick={() => toggleChecklist(c)} data-testid="founder-checklist-item"
                className="flex w-full items-center gap-2.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left transition-colors hover:bg-white/10">
                {c.done ? <CheckCircle2 size={17} className="text-[hsl(var(--primary))] shrink-0" /> : <Circle size={17} className="text-muted-foreground shrink-0" />}
                <span className={`text-sm ${c.done ? "line-through text-muted-foreground" : ""}`}>{c.item}</span>
              </button>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Tasks + Post */}
      <div className="grid gap-4 lg:grid-cols-12">
        <GlassCard className="rounded-2xl p-4 lg:col-span-7" data-testid="founder-tasks">
          <SectionTitle kicker="This week" title="Tasks" icon={Rocket} />
          <div className="mb-3 flex gap-2">
            <Input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTask(); } }}
              placeholder="Add a task…" className="bg-white/5 border-white/10" data-testid="founder-task-input" />
            <Button variant="secondary" onClick={addTask} data-testid="founder-add-task-button"><Plus size={16} /></Button>
          </div>
          <div className="space-y-2">
            {tasks.map((t) => (
              <div key={t.id} className="flex items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2" data-testid="founder-task-card">
                <span className={`min-w-0 flex-1 truncate text-sm ${t.status === "done" ? "line-through text-muted-foreground" : ""}`}>{t.title}</span>
                {t.priority && <StatusPill tone={PRIORITY_TONE[t.priority]} className="shrink-0 capitalize">{t.priority}</StatusPill>}
                <Select value={t.status} onValueChange={(v) => setTaskStatus(t, v)}>
                  <SelectTrigger className="h-8 w-[130px] bg-white/5 border-white/10 text-xs" data-testid="founder-task-status-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {STATUSES.map((s) => <SelectItem key={s} value={s}>{STATUS_LABEL[s]}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            ))}
            {tasks.length === 0 && <p className="text-sm text-muted-foreground">No tasks yet.</p>}
          </div>
        </GlassCard>

        <GlassCard className="rounded-2xl p-4 lg:col-span-5" data-testid="founder-post">
          <SectionTitle kicker="Build in public" title="Draft a launch post" icon={Megaphone} />
          <Textarea value={topic} onChange={(e) => setTopic(e.target.value)} rows={3} className="bg-white/5 border-white/10"
            placeholder="Angle (optional): launch announcement + demo, building in public…" data-testid="founder-post-topic-input" />
          <Button className="mt-3 w-full gap-1.5" disabled={busy} onClick={draftPost} data-testid="founder-draft-post-button">
            <PenLine size={15} /> {busy ? "Drafting…" : "Draft LinkedIn post"}
          </Button>
          <p className="mt-2 text-[11px] text-muted-foreground">Kaelra prepares the post; it only publishes after your approval.</p>
        </GlassCard>
      </div>

      <Dialog open={!!result} onOpenChange={(o) => !o && setResult(null)}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <Sparkles size={16} className="text-[hsl(var(--primary))]" /> {result?.title}
            </DialogTitle>
          </DialogHeader>
          <div className="whitespace-pre-line rounded-xl border border-white/10 bg-white/5 p-3 text-sm leading-relaxed">{result?.body}</div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
