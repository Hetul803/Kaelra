import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  GraduationCap, BookOpen, CalendarClock, Plus, Sparkles, Mail, MapPin, ClipboardList,
} from "lucide-react";

const STATUSES = ["todo", "in_progress", "done"];
const STATUS_LABEL = { todo: "To do", in_progress: "In progress", done: "Done" };
const PRIORITY_TONE = { high: "red", medium: "amber", low: "default" };

export default function ClassSkill() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [plan, setPlan] = useState(null);
  const [emailFor, setEmailFor] = useState(null);
  const [note, setNote] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState({ title: "", course: "", due: "", priority: "medium" });

  const load = useCallback(async () => {
    const { data } = await api.get("/class");
    setData(data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const setStatus = async (a, status) => {
    setBusyId(a.id);
    try {
      await api.post(`/class/assignments/${a.id}/status`, { status });
      await load();
    } catch (e) { toast.error("Couldn't update assignment."); }
    finally { setBusyId(null); }
  };

  const studyPlan = async (a) => {
    setBusyId(a.id);
    try {
      const { data } = await api.post(`/class/assignments/${a.id}/study-plan`);
      setPlan({ title: a.title, body: data.plan });
      toast.success("Study plan prepared and added to your Action Queue.");
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't build a study plan."); }
    finally { setBusyId(null); }
  };

  const addAssignment = async () => {
    if (!form.title.trim()) { toast.error("Give the assignment a title."); return; }
    try {
      await api.post("/class/assignments", form);
      setAddOpen(false);
      setForm({ title: "", course: "", due: "", priority: "medium" });
      await load();
      toast.success("Assignment added.");
    } catch (e) { toast.error("Couldn't add assignment."); }
  };

  const sendProfessorEmail = async () => {
    if (!note.trim()) { toast.error("Add a little context for the email."); return; }
    const cls = emailFor;
    setEmailFor(null);
    try {
      const { data } = await api.post(`/class/${cls.id}/professor-reply`, { note });
      setNote("");
      setPlan({ title: `Email to ${cls.professor}`, body: data.draft });
      toast.success("Email draft prepared — waiting for approval in the Action Queue.");
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't draft that email."); }
  };

  if (loading) return <LoadingState label="Loading your classes…" />;

  const classes = data?.classes || [];
  const assignments = data?.assignments || [];

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div>
        <div className="kaelra-kicker">School</div>
        <h1 className="font-heading text-2xl">Class &amp; School</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your classes, deadlines and study plans — Kaelra drafts professor emails and keeps you ahead of due dates.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Classes */}
        <GlassCard className="rounded-2xl p-4" data-testid="class-list">
          <SectionTitle kicker="This term" title="Your classes" icon={BookOpen} />
          <div className="space-y-2">
            {classes.map((c) => (
              <div key={c.id} className="rounded-xl border border-white/10 bg-white/5 p-3" data-testid="class-card">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-heading text-sm truncate">{c.name}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-3 text-xs text-muted-foreground">
                      <span>{c.professor}</span>
                      <span className="inline-flex items-center gap-1"><CalendarClock size={12} /> {c.schedule}</span>
                      {c.location && <span className="inline-flex items-center gap-1"><MapPin size={12} /> {c.location}</span>}
                    </div>
                  </div>
                  <Button size="sm" variant="secondary" className="h-8 shrink-0 gap-1.5 text-xs"
                    onClick={() => { setEmailFor(c); setNote(""); }} data-testid="class-email-prof-button">
                    <Mail size={13} /> Email
                  </Button>
                </div>
              </div>
            ))}
            {classes.length === 0 && <p className="text-sm text-muted-foreground">No classes yet.</p>}
          </div>
        </GlassCard>

        {/* Assignments */}
        <GlassCard className="rounded-2xl p-4" data-testid="assignment-list">
          <SectionTitle kicker="Stay ahead" title="Assignments" icon={ClipboardList}
            action={
              <Dialog open={addOpen} onOpenChange={setAddOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" variant="ghost" className="gap-1 text-xs" data-testid="class-add-assignment-button"><Plus size={14} /> Add</Button>
                </DialogTrigger>
                <DialogContent className="glass-strong border-white/10">
                  <DialogHeader><DialogTitle className="font-heading">New assignment</DialogTitle></DialogHeader>
                  <div className="space-y-3">
                    <div><Label className="mb-1 block">Title</Label>
                      <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                        className="bg-white/5 border-white/10" placeholder="Assignment 4 (GraphQL)" data-testid="assignment-title-input" /></div>
                    <div className="grid grid-cols-2 gap-3">
                      <div><Label className="mb-1 block">Course</Label>
                        <Input value={form.course} onChange={(e) => setForm({ ...form, course: e.target.value })}
                          className="bg-white/5 border-white/10" placeholder="CS-401" /></div>
                      <div><Label className="mb-1 block">Due</Label>
                        <Input value={form.due} onChange={(e) => setForm({ ...form, due: e.target.value })}
                          className="bg-white/5 border-white/10" placeholder="Oct 30" /></div>
                    </div>
                    <div><Label className="mb-1 block">Priority</Label>
                      <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
                        <SelectTrigger className="bg-white/5 border-white/10 capitalize"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {["high", "medium", "low"].map((p) => <SelectItem key={p} value={p} className="capitalize">{p}</SelectItem>)}
                        </SelectContent>
                      </Select></div>
                  </div>
                  <DialogFooter>
                    <Button onClick={addAssignment} data-testid="assignment-save-button">Add assignment</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            } />
          <div className="space-y-2">
            {assignments.map((a) => (
              <div key={a.id} className="rounded-xl border border-white/10 bg-white/5 p-3" data-testid="assignment-card">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className={`text-sm font-medium truncate ${a.status === "done" ? "line-through text-muted-foreground" : ""}`}>{a.title}</div>
                    <div className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      {a.course && <span>{a.course}</span>}
                      {a.due && <span className="inline-flex items-center gap-1"><CalendarClock size={12} /> {a.due}</span>}
                    </div>
                  </div>
                  {a.priority && <StatusPill tone={PRIORITY_TONE[a.priority]} className="shrink-0 capitalize">{a.priority}</StatusPill>}
                </div>
                <div className="mt-2.5 flex flex-wrap items-center gap-2">
                  <Select value={a.status} onValueChange={(v) => setStatus(a, v)} disabled={busyId === a.id}>
                    <SelectTrigger className="h-8 w-[140px] bg-white/5 border-white/10 text-xs" data-testid="assignment-status-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {STATUSES.map((s) => <SelectItem key={s} value={s}>{STATUS_LABEL[s]}</SelectItem>)}
                    </SelectContent>
                  </Select>
                  <Button size="sm" variant="secondary" className="h-8 gap-1.5 text-xs" disabled={busyId === a.id}
                    onClick={() => studyPlan(a)} data-testid="assignment-study-plan-button">
                    <Sparkles size={13} /> Study plan
                  </Button>
                </div>
              </div>
            ))}
            {assignments.length === 0 && <p className="text-sm text-muted-foreground">No assignments tracked yet.</p>}
          </div>
        </GlassCard>
      </div>

      {/* Email professor dialog */}
      <Dialog open={!!emailFor} onOpenChange={(o) => !o && setEmailFor(null)}>
        <DialogContent className="glass-strong border-white/10" data-testid="class-email-dialog">
          <DialogHeader><DialogTitle className="font-heading">Email {emailFor?.professor}</DialogTitle></DialogHeader>
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">What's this about? Kaelra will draft a respectful email — nothing sends without your approval.</Label>
            <Textarea value={note} onChange={(e) => setNote(e.target.value)} rows={4} className="bg-white/5 border-white/10"
              placeholder="Ask for a 2-day extension on Assignment 3 due to work shifts." data-testid="class-email-note-input" />
          </div>
          <DialogFooter>
            <Button onClick={sendProfessorEmail} className="gap-1.5" data-testid="class-email-draft-button"><Mail size={15} /> Draft email</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Plan / draft result dialog */}
      <Dialog open={!!plan} onOpenChange={(o) => !o && setPlan(null)}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <Sparkles size={16} className="text-[hsl(var(--primary))]" /> {plan?.title}
            </DialogTitle>
          </DialogHeader>
          <div className="whitespace-pre-line rounded-xl border border-white/10 bg-white/5 p-3 text-sm leading-relaxed">{plan?.body}</div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
