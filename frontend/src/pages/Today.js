import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { ActionCard } from "../components/ActionCard";
import { Button } from "../components/ui/button";
import { Progress } from "../components/ui/progress";
import {
  CalendarDays, Mail, Car, Bell, Newspaper, Target, FolderOpen, ListChecks,
  MonitorSmartphone, RefreshCw, MapPin, Cloud, ArrowRight, Laptop, Smartphone, Tablet,
} from "lucide-react";

function CardShell({ children, className = "", testid }) {
  return <GlassCard className={`rounded-2xl p-4 ${className}`} data-testid={testid}>{children}</GlassCard>;
}

const deviceIcon = (k) => (k === "phone" ? Smartphone : k === "tablet" ? Tablet : Laptop);

export default function Today() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/dashboard");
    setData(data);
    return data;
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await load();
      toast.success("Control panel refreshed.");
    } catch (e) {
      toast.error("Couldn't refresh right now.");
    } finally {
      setRefreshing(false);
    }
  }, [load]);

  useEffect(() => {
    (async () => {
      try { await load(); } finally { setLoading(false); }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateAction = async (id, payload) => {
    await api.put(`/actions/${id}`, payload);
    await load();
    triggerKaelraRefresh();
  };

  if (loading) return <LoadingState label="Kaelra is checking your day…" />;

  const cards = data?.cards || {};
  const events = cards.calendar?.events || [];
  const importantEmails = cards.emails?.important || [];
  const commute = cards.commute;
  const news = cards.news?.articles || [];
  const goals = cards.goals || [];
  const reminders = cards.reminders || [];
  const filesNeeding = cards.files_needing_attention || [];
  const pending = (cards.pending_actions || []).slice(0, 3);
  const devices = data?.devices || [];

  return (
    <div className="mx-auto max-w-[1200px] space-y-5">
      {/* Control panel header */}
      <div className="grid gap-4 lg:grid-cols-12">
        <GlassCard className="rounded-2xl p-5 lg:col-span-8" data-testid="today-control-panel-header">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <span className="kaelra-kicker">Control panel</span>
              <h2 className="mt-1 font-heading text-xl md:text-2xl">Your day at a glance</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                The raw data behind Kaelra. For the conversation, head to{" "}
                <Link to="/" className="text-[hsl(var(--primary))] hover:underline">Kaelra</Link>.
              </p>
            </div>
            <Button size="sm" variant="ghost" className="shrink-0 gap-1.5 text-xs" disabled={refreshing}
              onClick={refresh} data-testid="today-refresh-data">
              <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} /> Refresh
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <StatusPill tone="teal" data-testid="cp-stat-actions"><ListChecks size={12} /> {data?.action_counts?.pending || 0} pending</StatusPill>
            <StatusPill><CalendarDays size={12} /> {events.length} events</StatusPill>
            <StatusPill><Mail size={12} /> {cards.emails?.unread_count || 0} unread</StatusPill>
            <StatusPill><FolderOpen size={12} /> {filesNeeding.length} files need attention</StatusPill>
          </div>
        </GlassCard>

        {/* Action queue preview */}
        <GlassCard className="rounded-2xl p-4 lg:col-span-4" data-testid="today-action-queue-preview">
          <SectionTitle kicker="Waiting for you" title="Action Queue" icon={ListChecks}
            action={<Link to="/queue"><Button size="sm" variant="ghost" className="gap-1 text-xs">All <ArrowRight size={13} /></Button></Link>} />
          <div className="space-y-2">
            {pending.length === 0 && <p className="text-sm text-muted-foreground py-4 text-center">Nothing waiting. You’re clear.</p>}
            {pending.map((a) => (
              <div key={a.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium truncate">{a.title}</span>
                  {a.sensitive && <StatusPill tone="sensitive" className="shrink-0">approval</StatusPill>}
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{a.what}</p>
                <div className="mt-2 flex gap-2">
                  <Button size="sm" className="h-7 px-2 text-xs gap-1" onClick={() => updateAction(a.id, { status: "approved" })}>Approve</Button>
                  <Button size="sm" variant="secondary" className="h-7 px-2 text-xs" onClick={() => updateAction(a.id, { status: "rejected" })}>Reject</Button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Card grid */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {/* Schedule */}
        <CardShell testid="card-schedule">
          <SectionTitle kicker="Today" title="Schedule" icon={CalendarDays} />
          <div className="space-y-2">
            {events.map((e) => (
              <div key={e.id} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="text-right">
                  <div className="text-sm font-medium">{e.start}</div>
                  <div className="text-[11px] text-muted-foreground">{e.end}</div>
                </div>
                <div className="h-8 w-px bg-white/10" />
                <div className="min-w-0">
                  <div className="truncate text-sm">{e.title}</div>
                  <div className="truncate text-xs text-muted-foreground">{e.location}</div>
                </div>
              </div>
            ))}
            {events.length === 0 && <p className="text-sm text-muted-foreground">No events today.</p>}
          </div>
        </CardShell>

        {/* Important emails */}
        <CardShell testid="card-emails">
          <SectionTitle kicker={`${cards.emails?.unread_count || 0} unread`} title="Important emails" icon={Mail} />
          <div className="space-y-2">
            {importantEmails.map((m) => (
              <div key={m.id} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium">{m.from}</span>
                  {m.monitored && <StatusPill tone="amber" className="shrink-0">monitored</StatusPill>}
                  {m.needs_reply && <StatusPill tone="teal" className="shrink-0">reply?</StatusPill>}
                </div>
                <div className="truncate text-sm">{m.subject}</div>
                <div className="line-clamp-1 text-xs text-muted-foreground">{m.snippet}</div>
              </div>
            ))}
            {importantEmails.length === 0 && <p className="text-sm text-muted-foreground">Inbox is calm.</p>}
          </div>
        </CardShell>

        {/* Commute */}
        <CardShell testid="card-commute">
          <SectionTitle kicker="Leave-time" title="Commute" icon={Car} />
          {commute ? (
            <div>
              <div className="flex items-end gap-2">
                <span className="font-heading text-3xl text-[hsl(var(--primary))]">{commute.leave_by}</span>
                <span className="mb-1 text-xs text-muted-foreground">leave by</span>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">
                {commute.commute_minutes} min to {commute.destination} for your {commute.event_start} {commute.event_title}.
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                <StatusPill><MapPin size={12} /> {commute.traffic} traffic</StatusPill>
                <StatusPill><Cloud size={12} /> {commute.weather?.summary}</StatusPill>
              </div>
            </div>
          ) : <p className="text-sm text-muted-foreground">No commute planned.</p>}
        </CardShell>

        {/* Goals */}
        <CardShell testid="card-goals">
          <SectionTitle kicker="Progress" title="Goals" icon={Target}
            action={<Link to="/memory"><Button size="sm" variant="ghost" className="text-xs">Manage</Button></Link>} />
          <div className="space-y-3">
            {goals.slice(0, 4).map((g) => (
              <div key={g.id}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="truncate">{g.title}</span>
                  <span className="text-xs text-muted-foreground">{Math.round((g.progress || 0) * 100)}%</span>
                </div>
                <Progress value={(g.progress || 0) * 100} className="h-1.5 bg-white/10" />
              </div>
            ))}
            {goals.length === 0 && <p className="text-sm text-muted-foreground">No goals yet.</p>}
          </div>
        </CardShell>

        {/* Reminders */}
        <CardShell testid="card-reminders">
          <SectionTitle kicker="Notifications" title="Reminders" icon={Bell}
            action={<Link to="/routines"><Button size="sm" variant="ghost" className="text-xs">Routines</Button></Link>} />
          <div className="space-y-2">
            {reminders.slice(0, 4).map((r) => (
              <div key={r.id} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <Bell size={14} className="text-[hsl(var(--primary))]" />
                <span className="truncate text-sm">{r.title}</span>
              </div>
            ))}
            {reminders.length === 0 && <p className="text-sm text-muted-foreground">No reminders set. Approve a commute alert and I’ll add one.</p>}
          </div>
        </CardShell>

        {/* News */}
        <CardShell testid="card-news">
          <SectionTitle kicker="For you" title="News briefing" icon={Newspaper} />
          <div className="space-y-2">
            {news.slice(0, 4).map((a, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="text-sm leading-snug">{a.title}</div>
                <div className="text-[11px] text-muted-foreground font-mono-k">{a.source} · {a.interest}</div>
              </div>
            ))}
            {news.length === 0 && <p className="text-sm text-muted-foreground">No news today.</p>}
          </div>
        </CardShell>

        {/* Files needing attention */}
        <CardShell testid="card-files">
          <SectionTitle kicker="Attention" title="Files" icon={FolderOpen}
            action={<Link to="/files"><Button size="sm" variant="ghost" className="text-xs">Open</Button></Link>} />
          <div className="space-y-2">
            {filesNeeding.map((f) => (
              <div key={f.id} className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                <div className="truncate text-sm">{f.name}</div>
                <div className="line-clamp-1 text-xs text-muted-foreground">{f.reason}</div>
              </div>
            ))}
            {filesNeeding.length === 0 && <p className="text-sm text-muted-foreground">No files need attention.</p>}
          </div>
        </CardShell>

        {/* Device sync */}
        <CardShell testid="today-device-sync-status">
          <SectionTitle kicker="Synced" title="Devices" icon={MonitorSmartphone}
            action={<Link to="/devices"><Button size="sm" variant="ghost" className="text-xs">Manage</Button></Link>} />
          <div className="space-y-2">
            {devices.slice(0, 3).map((d) => {
              const Icon = deviceIcon(d.kind);
              return (
                <div key={d.id} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                  <Icon size={16} className="text-[hsl(var(--primary))]" />
                  <span className="flex-1 truncate text-sm">{d.name}</span>
                  <span className="h-2 w-2 rounded-full bg-[hsl(var(--primary))] animate-pulse" />
                </div>
              );
            })}
            {devices.length === 0 && <p className="text-sm text-muted-foreground">No synced devices yet.</p>}
          </div>
        </CardShell>
      </div>
    </div>
  );
}
