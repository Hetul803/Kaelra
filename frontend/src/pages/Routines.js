import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { GlassCard, SectionTitle, EmptyState, LoadingState, StatusPill } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "../components/ui/dialog";
import { Bell, Plus, Trash2, Repeat, Sun, Car, Mail, CalendarClock, Newspaper, Moon } from "lucide-react";

const TYPE_ICON = {
  briefing: Sun, commute: Car, email_monitor: Mail, deadline: CalendarClock,
  news: Newspaper, prep: Moon, general: Repeat,
};

export default function Routines() {
  const [routines, setRoutines] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", schedule: "", type: "general", enabled: true });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r, n] = await Promise.all([api.get("/routines"), api.get("/notifications")]);
      setRoutines(r.data); setNotifications(n.data);
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const toggle = async (r) => { await api.put(`/routines/${r.id}`, { enabled: !r.enabled }); load(); };
  const remove = async (r) => { await api.delete(`/routines/${r.id}`); toast.success("Routine removed."); load(); };
  const add = async () => {
    if (!form.name.trim()) { toast.error("Give the routine a name."); return; }
    await api.post("/routines", form);
    toast.success("Routine added."); setOpen(false);
    setForm({ name: "", description: "", schedule: "", type: "general", enabled: true });
    load();
  };
  const removeNote = async (n) => { await api.delete(`/notifications/${n.id}`); load(); };

  if (loading) return <LoadingState label="Loading routines…" />;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="kaelra-kicker">Proactive Kaelra</div>
          <h1 className="font-heading text-2xl">Routines & Notifications</h1>
          <p className="mt-1 text-sm text-muted-foreground">Tell Kaelra what to watch and when to reach out.</p>
        </div>
        <Button onClick={() => setOpen(true)} className="gap-1.5" data-testid="routine-add-button"><Plus size={16} /> New routine</Button>
      </div>

      <div className="space-y-3">
        {routines.length === 0 && (
          <EmptyState icon={Bell} title="No routines yet" hint="Add a morning briefing or an email watcher." />
        )}
        {routines.map((r) => {
          const Icon = TYPE_ICON[r.type] || Repeat;
          return (
            <GlassCard key={r.id} className="rounded-2xl p-4" data-testid="routine-card">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]"><Icon size={18} /></span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-heading">{r.name}</span>
                    {r.schedule && <StatusPill>{r.schedule}</StatusPill>}
                  </div>
                  {r.description && <p className="truncate text-xs text-muted-foreground">{r.description}</p>}
                </div>
                <Switch checked={r.enabled} onCheckedChange={() => toggle(r)} data-testid="routine-toggle" />
                <Button size="icon" variant="ghost" onClick={() => remove(r)} aria-label="Delete"><Trash2 size={15} /></Button>
              </div>
            </GlassCard>
          );
        })}
      </div>

      <div>
        <SectionTitle kicker="Scheduled" title="Reminders" icon={Bell} />
        <div className="space-y-2">
          {notifications.length === 0 && <p className="text-sm text-muted-foreground">No reminders yet. Approve a commute alert and Kaelra will schedule one.</p>}
          {notifications.map((n) => (
            <GlassCard key={n.id} className="rounded-xl p-3">
              <div className="flex items-center gap-2">
                <Bell size={14} className="text-[hsl(var(--primary))]" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm">{n.title}</div>
                  {n.body && <div className="truncate text-xs text-muted-foreground">{n.body}</div>}
                </div>
                {n.scheduled_for && <StatusPill>{n.scheduled_for}</StatusPill>}
                <Button size="icon" variant="ghost" onClick={() => removeNote(n)} aria-label="Delete"><Trash2 size={14} /></Button>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader><DialogTitle>New routine</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div><Label className="mb-1 block">Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Morning briefing" className="bg-white/5 border-white/10" data-testid="routine-name-input" /></div>
            <div><Label className="mb-1 block">Description</Label>
              <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Brief me on what matters today" className="bg-white/5 border-white/10" /></div>
            <div><Label className="mb-1 block">Schedule / trigger</Label>
              <Input value={form.schedule} onChange={(e) => setForm({ ...form, schedule: e.target.value })} placeholder="6:00 AM" className="bg-white/5 border-white/10" /></div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={add} data-testid="routine-save-button">Add routine</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
