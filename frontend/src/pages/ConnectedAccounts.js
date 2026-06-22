import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { GlassCard, StatusPill, LoadingState } from "../components/Bits";
import { ContextBuilder } from "../components/ContextBuilder";
import { Button } from "../components/ui/button";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Calendar, Mail, FolderOpen, MapPin, Newspaper, Bell, Github, Home, Plug,
  ShieldCheck, RefreshCw, Link2, Sparkles,
} from "lucide-react";

const ICONS = {
  calendar: Calendar, mail: Mail, folder: FolderOpen, "map-pin": MapPin,
  newspaper: Newspaper, bell: Bell, github: Github, home: Home,
};

const STATE_META = {
  connected: { tone: "green", label: "Connected" },
  not_connected: { tone: "default", label: "Not connected" },
  needs_attention: { tone: "amber", label: "Needs attention" },
  coming_soon: { tone: "teal", label: "Coming soon" },
};

const GOOGLE_PROVIDERS = ["google_calendar", "gmail", "google_drive"];
const GOOGLE_SCOPE_CHIPS = [
  { icon: Calendar, label: "Calendar" },
  { icon: Mail, label: "Gmail" },
  { icon: FolderOpen, label: "Drive" },
];

export default function ConnectedAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [google, setGoogle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [rebuildOpen, setRebuildOpen] = useState(false);

  const load = useCallback(async () => {
    const [acc, g] = await Promise.all([
      api.get("/accounts"),
      api.get("/oauth/google/status").catch(() => ({ data: { configured: false, connected: false } })),
    ]);
    setAccounts(acc.data);
    setGoogle(g.data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const startGoogle = async () => {
    setConnecting(true);
    try {
      const redirect_uri = window.location.origin + "/auth/google";
      const { data } = await api.get("/oauth/google/url", { params: { redirect_uri } });
      window.location.href = data.url;
    } catch (e) {
      setConnecting(false);
      toast.error(e?.response?.data?.detail || "Google isn't configured yet.");
    }
  };

  const disconnectGoogle = async () => {
    try {
      await api.post("/oauth/google/disconnect");
      toast.success("Disconnected your Google account.");
      await load();
    } catch (e) { toast.error("Couldn't disconnect."); }
  };

  const setStatus = async (provider, status) => {
    try {
      await api.put(`/accounts/${provider}`, { status });
      toast.success(status === "connected" ? "Connected." : "Disconnected.");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Couldn't update."); }
  };

  if (loading) return <LoadingState label="Loading connectors…" />;

  const connected = !!google?.connected;
  const configured = !!google?.configured;
  const otherAccounts = accounts.filter((a) => !GOOGLE_PROVIDERS.includes(a.provider));

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div>
        <div className="kaelra-kicker">Kaelra's skills</div>
        <h1 className="font-heading text-2xl">Connected Accounts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your Google account so Kaelra can work from your real calendar, email and files — with approval gates on anything sensitive.
        </p>
      </div>

      {/* Google hero */}
      <GlassCard className="rounded-2xl p-5" data-testid="google-connect-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]">
              <Link2 size={22} />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-heading text-lg">Google Workspace</h2>
                <StatusPill tone={connected ? "green" : "default"}>
                  {connected ? "Connected" : "Not connected"}
                </StatusPill>
              </div>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {connected
                  ? <>Reading from <span className="font-mono-k text-foreground/90">{google.email}</span></>
                  : "Calendar, Gmail and Drive in one secure connection."}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {GOOGLE_SCOPE_CHIPS.map(({ icon: Icon, label }) => (
                  <span key={label}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${
                      connected
                        ? "border-[rgba(45,212,191,0.22)] bg-[rgba(45,212,191,0.12)] text-[rgb(153,246,228)]"
                        : "border-white/10 bg-white/5 text-muted-foreground"}`}>
                    <Icon size={13} /> {label}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="flex shrink-0 flex-col gap-2 sm:items-end">
            {connected ? (
              <>
                <Button variant="secondary" className="gap-1.5" onClick={() => setRebuildOpen(true)} data-testid="google-rebuild-context-button">
                  <RefreshCw size={15} /> Rebuild context
                </Button>
                <Button variant="ghost" className="gap-1.5 text-[rgb(254,202,202)]" onClick={disconnectGoogle} data-testid="google-disconnect-button">
                  Disconnect
                </Button>
              </>
            ) : (
              <Button className="gap-1.5" disabled={connecting} onClick={startGoogle} data-testid="google-connect-button">
                <Sparkles size={16} /> {connecting ? "Opening Google…" : "Connect Google"}
              </Button>
            )}
          </div>
        </div>

        <div className="mt-4 flex items-start gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
          <ShieldCheck size={15} className="mt-0.5 shrink-0 text-[hsl(var(--primary))]" />
          <p className="text-xs text-muted-foreground">
            {configured
              ? "Least-privilege access. Kaelra only reads the sources you connect, drafts (never sends) emails, and asks approval before anything leaves your account."
              : "Google credentials aren't configured on the server yet — Kaelra is running on realistic demo data. Add them to switch on the real connection."}
          </p>
        </div>
      </GlassCard>

      {/* Other connectors */}
      <div>
        <div className="kaelra-kicker mb-2">More connectors</div>
        <div className="grid gap-3 sm:grid-cols-2">
          {otherAccounts.map((a) => {
            const Icon = ICONS[a.icon] || Plug;
            const meta = STATE_META[a.status] || STATE_META.not_connected;
            return (
              <GlassCard key={a.id} className="rounded-2xl p-4" data-testid="integration-card">
                <div className="flex items-start gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]"><Icon size={20} /></span>
                  <div className="min-w-0 flex-1">
                    <div className="font-heading">{a.name}</div>
                    <div className="text-xs text-muted-foreground">{a.category}</div>
                  </div>
                  <StatusPill tone={meta.tone}>{meta.label}</StatusPill>
                </div>
                <div className="mt-3">
                  {a.status === "coming_soon" ? (
                    <Button size="sm" variant="secondary" disabled className="w-full">Coming soon</Button>
                  ) : a.status === "connected" ? (
                    <Button size="sm" variant="secondary" className="w-full" onClick={() => setStatus(a.provider, "not_connected")} data-testid="integration-disconnect-button">Disconnect</Button>
                  ) : (
                    <Button size="sm" className="w-full" onClick={() => setStatus(a.provider, "connected")} data-testid="integration-connect-button">Connect</Button>
                  )}
                </div>
              </GlassCard>
            );
          })}
        </div>
      </div>

      {/* Rebuild context dialog */}
      <Dialog open={rebuildOpen} onOpenChange={setRebuildOpen}>
        <DialogContent className="glass-strong border-white/10" data-testid="rebuild-context-dialog">
          <DialogHeader>
            <DialogTitle className="font-heading">Rebuilding your context</DialogTitle>
          </DialogHeader>
          {rebuildOpen && <ContextBuilder onDone={() => { setRebuildOpen(false); load(); }} doneLabel="Done" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
