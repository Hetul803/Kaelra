import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { formatDistanceToNow, parseISO } from "date-fns";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { GlassCard, SectionTitle, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "../components/ui/alert-dialog";
import {
  User, Sparkles, ShieldCheck, Bell, Mic, Download, Trash2, ScrollText, Save,
} from "lucide-react";

const TONES = ["calm", "friendly", "direct", "energetic"];
const APPROVAL_KEYS = [
  ["emails", "Sending emails"],
  ["jobs", "Applying to jobs"],
  ["calendar", "Changing calendar events"],
  ["files", "Deleting / moving files"],
  ["purchases", "Making purchases"],
];

export default function Settings() {
  const { user, refreshProfile } = useAuth();
  const [profile, setProfile] = useState(null);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [me, a] = await Promise.all([api.get("/auth/me"), api.get("/audit")]);
      setProfile(me.data.profile || {});
      setAudit(a.data);
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const set = (k, v) => setProfile((p) => ({ ...p, [k]: v }));
  const setApproval = (k, v) => setProfile((p) => ({ ...p, approval_rules: { ...(p.approval_rules || {}), [k]: v } }));

  const save = async () => {
    setSaving(true);
    try {
      await api.put("/settings", {
        name: profile.name, call_me: profile.call_me, tone: profile.tone,
        notifications_enabled: profile.notifications_enabled, device_sync: profile.device_sync,
        proactive_briefing: profile.proactive_briefing, voice_enabled: profile.voice_enabled,
        approval_rules: profile.approval_rules,
      });
      await refreshProfile();
      toast.success("Settings saved.");
    } catch (e) { toast.error("Couldn't save settings."); }
    finally { setSaving(false); }
  };

  const exportData = async () => {
    const { data } = await api.get("/privacy/export");
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "kaelra-data-export.json"; a.click();
    URL.revokeObjectURL(url);
    toast.success("Your data export is downloading.");
  };

  const deleteData = async () => {
    await api.delete("/privacy/data");
    toast.success("All Kaelra-stored data deleted.");
    load();
  };

  if (loading || !profile) return <LoadingState label="Loading settings…" />;

  const Toggle = ({ k, icon: Icon, label, desc }) => (
    <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon size={16} className="text-[hsl(var(--primary))]" />
        <div><div className="text-sm">{label}</div><div className="text-xs text-muted-foreground">{desc}</div></div>
      </div>
      <Switch checked={!!profile[k]} onCheckedChange={(v) => set(k, v)} data-testid={`settings-toggle-${k}`} />
    </div>
  );

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="kaelra-kicker">You’re in control</div>
          <h1 className="font-heading text-2xl">Settings & Privacy</h1>
        </div>
        <Button onClick={save} disabled={saving} className="gap-1.5" data-testid="settings-save-button">
          <Save size={16} /> {saving ? "Saving…" : "Save"}
        </Button>
      </div>

      {/* Profile */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Profile" title="About you" icon={User} />
        <div className="grid gap-3 sm:grid-cols-2">
          <div><Label className="mb-1 block">Name</Label>
            <Input value={profile.name || ""} onChange={(e) => set("name", e.target.value)} className="bg-white/5 border-white/10" data-testid="settings-name-input" /></div>
          <div><Label className="mb-1 block">What Kaelra calls you</Label>
            <Input value={profile.call_me || ""} onChange={(e) => set("call_me", e.target.value)} className="bg-white/5 border-white/10" /></div>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">{user?.email}</p>
      </GlassCard>

      {/* Personality */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Personality" title="Kaelra’s tone" icon={Sparkles} />
        <Select value={profile.tone || "friendly"} onValueChange={(v) => set("tone", v)}>
          <SelectTrigger className="bg-white/5 border-white/10 capitalize" data-testid="settings-tone-select"><SelectValue /></SelectTrigger>
          <SelectContent>
            {TONES.map((t) => <SelectItem key={t} value={t} className="capitalize">{t}</SelectItem>)}
          </SelectContent>
        </Select>
      </GlassCard>

      {/* Preferences */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Preferences" title="How Kaelra reaches you" icon={Bell} />
        <div className="space-y-2">
          <Toggle k="proactive_briefing" icon={Sparkles} label="Proactive morning briefing" desc="Prepare my day before I ask." />
          <Toggle k="notifications_enabled" icon={Bell} label="Notifications & reminders" desc="Leave-times, deadlines, important changes." />
          <Toggle k="device_sync" icon={ShieldCheck} label="Phone & laptop sync" desc="Continue seamlessly across devices." />
          <Toggle k="voice_enabled" icon={Mic} label="Voice mode (preview)" desc="Voice-ready UI — live voice coming soon." />
        </div>
      </GlassCard>

      {/* Approval rules */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Safety" title="Approval rules" icon={ShieldCheck} />
        <p className="mb-3 text-sm text-muted-foreground">Kaelra always asks before these. Keep them on for full control.</p>
        <div className="space-y-2">
          {APPROVAL_KEYS.map(([k, label]) => (
            <div key={k} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
              <span className="text-sm">{label}</span>
              <Switch checked={profile.approval_rules?.[k] ?? true} onCheckedChange={(v) => setApproval(k, v)} data-testid={`settings-approval-${k}`} />
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Data controls */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Privacy" title="Your data" icon={Download} />
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={exportData} className="gap-1.5" data-testid="settings-export-data-button">
            <Download size={16} /> Export my data
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="secondary" className="gap-1.5 text-[rgb(254,202,202)]" data-testid="settings-delete-data-button">
                <Trash2 size={16} /> Delete my data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="glass-strong border-white/10">
              <AlertDialogHeader>
                <AlertDialogTitle>Delete all your data?</AlertDialogTitle>
                <AlertDialogDescription>
                  This permanently removes your memories, goals, routines, actions, files, conversations and history. Your account stays.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Keep</AlertDialogCancel>
                <AlertDialogAction onClick={deleteData}>Delete everything</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </GlassCard>

      {/* Audit log */}
      <GlassCard className="rounded-2xl p-5">
        <SectionTitle kicker="Transparency" title="Audit log" icon={ScrollText} />
        <div className="space-y-1.5 max-h-80 overflow-y-auto" data-testid="settings-audit-log">
          {audit.length === 0 && <p className="text-sm text-muted-foreground">No activity yet.</p>}
          {audit.map((e) => (
            <div key={e.id} className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2">
              <span className="font-mono-k text-[11px] text-[hsl(var(--primary))]">{e.event}</span>
              <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{e.detail}</span>
              <span className="shrink-0 text-[11px] text-muted-foreground font-mono-k">
                {e.created_at ? formatDistanceToNow(parseISO(e.created_at), { addSuffix: true }) : ""}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
