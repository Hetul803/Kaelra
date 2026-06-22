import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Briefcase, FileText, Building2, MapPin, Send, Sparkles, BadgeCheck, Wallet,
} from "lucide-react";

const PIPELINE_COLS = ["saved", "applied", "interviewing", "offer", "rejected"];
const ALL_STATUSES = ["matched", "saved", "applied", "interviewing", "offer", "rejected"];
const TONE = {
  matched: "teal", saved: "default", applied: "teal",
  interviewing: "amber", offer: "green", rejected: "red",
};

function JobCard({ job, onStatus, onReply, busy }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3.5" data-testid="job-card">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-heading text-sm truncate">{job.title}</div>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1"><Building2 size={12} /> {job.company}</span>
            <span className="inline-flex items-center gap-1"><MapPin size={12} /> {job.location}</span>
            {job.salary && <span className="inline-flex items-center gap-1"><Wallet size={12} /> {job.salary}</span>}
          </div>
        </div>
        {typeof job.match === "number" && (
          <StatusPill tone="teal" className="shrink-0">{Math.round(job.match * 100)}% match</StatusPill>
        )}
      </div>

      {job.tags?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {job.tags.map((t) => (
            <span key={t} className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-muted-foreground">{t}</span>
          ))}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Select value={job.status} onValueChange={(v) => onStatus(job, v)} disabled={busy}>
          <SelectTrigger className="h-8 w-[150px] bg-white/5 border-white/10 text-xs capitalize" data-testid="job-status-select">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ALL_STATUSES.map((s) => <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>)}
          </SelectContent>
        </Select>
        <Button size="sm" variant="secondary" className="h-8 gap-1.5 text-xs" disabled={busy}
          onClick={() => onReply(job)} data-testid="job-recruiter-reply-button">
          <Send size={13} /> Draft recruiter reply
        </Button>
      </div>
    </div>
  );
}

export default function Jobs() {
  const [data, setData] = useState(null);
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [draft, setDraft] = useState(null);

  const load = useCallback(async () => {
    const [o, r] = await Promise.all([api.get("/jobs"), api.get("/jobs/best-resume")]);
    setData(o.data);
    setResume(r.data.resume);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const onStatus = async (job, status) => {
    setBusyId(job.id);
    try {
      await api.post(`/jobs/${job.id}/status`, { status });
      toast.success(`Moved “${job.title}” to ${status}.`);
      await load();
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't update that application."); }
    finally { setBusyId(null); }
  };

  const onReply = async (job) => {
    setBusyId(job.id);
    try {
      const { data: res } = await api.post(`/jobs/${job.id}/recruiter-reply`);
      setDraft({ title: job.title, company: job.company, body: res.draft, resume: res.resume });
      toast.success("Draft prepared — waiting for your approval in the Action Queue.");
      triggerKaelraRefresh();
    } catch (e) { toast.error("Couldn't draft a reply right now."); }
    finally { setBusyId(null); }
  };

  if (loading) return <LoadingState label="Loading your job search…" />;

  const matches = data?.matches || [];
  const pipeline = data?.pipeline || {};
  const counts = data?.counts || {};

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div>
        <div className="kaelra-kicker">Career</div>
        <h1 className="font-heading text-2xl">Jobs &amp; Career</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Kaelra tracks matches, your pipeline, and prepares recruiter replies with your best resume — always approval-gated.
        </p>
      </div>

      {/* Best resume */}
      <GlassCard className="rounded-2xl p-4" data-testid="jobs-best-resume">
        <SectionTitle kicker="Kaelra recommends" title="Best resume to send" icon={FileText} />
        {resume ? (
          <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
            <BadgeCheck size={18} className="text-[hsl(var(--primary))] shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium">{resume.name}</div>
              <div className="truncate text-xs text-muted-foreground">{resume.reason}</div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No resume found yet. Upload one in Files or connect Drive, and Kaelra will pick the best one for each role.
          </p>
        )}
      </GlassCard>

      <Tabs defaultValue="matches">
        <TabsList className="bg-white/5" data-testid="jobs-tabs">
          <TabsTrigger value="matches">Matches ({matches.length})</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
        </TabsList>

        <TabsContent value="matches" className="mt-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {matches.map((j) => (
              <JobCard key={j.id} job={j} onStatus={onStatus} onReply={onReply} busy={busyId === j.id} />
            ))}
            {matches.length === 0 && (
              <p className="text-sm text-muted-foreground">No new matches — you've triaged them all.</p>
            )}
          </div>
        </TabsContent>

        <TabsContent value="pipeline" className="mt-4">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {PIPELINE_COLS.map((col) => (
              <GlassCard key={col} className="rounded-2xl p-3" data-testid="jobs-pipeline-column">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-heading text-sm capitalize">{col}</span>
                  <StatusPill tone={TONE[col]}>{counts[col] || 0}</StatusPill>
                </div>
                <div className="space-y-2">
                  {(pipeline[col] || []).map((j) => (
                    <JobCard key={j.id} job={j} onStatus={onStatus} onReply={onReply} busy={busyId === j.id} />
                  ))}
                  {(pipeline[col] || []).length === 0 && (
                    <p className="px-1 py-3 text-xs text-muted-foreground">Nothing here yet.</p>
                  )}
                </div>
              </GlassCard>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={!!draft} onOpenChange={(o) => !o && setDraft(null)}>
        <DialogContent className="glass-strong border-white/10" data-testid="jobs-draft-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading flex items-center gap-2">
              <Sparkles size={16} className="text-[hsl(var(--primary))]" /> Recruiter reply prepared
            </DialogTitle>
          </DialogHeader>
          {draft && (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">For {draft.title} @ {draft.company}. Kaelra will not send this until you approve it in the Action Queue.</p>
              <div className="whitespace-pre-line rounded-xl border border-white/10 bg-white/5 p-3 text-sm leading-relaxed">{draft.body}</div>
              {draft.resume && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <FileText size={13} className="text-[hsl(var(--primary))]" /> Attaches: {draft.resume.name}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
