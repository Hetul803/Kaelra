import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { GlassCard, LoadingState, StatusPill } from "../components/Bits";
import { Button } from "../components/ui/button";
import {
  Calendar, Mail, FolderOpen, MapPin, Newspaper, Bell, Github, Home, Plug,
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

export default function ConnectedAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { const { data } = await api.get("/accounts"); setAccounts(data); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const setStatus = async (provider, status) => {
    try {
      await api.put(`/accounts/${provider}`, { status });
      toast.success(status === "connected" ? "Connected." : "Disconnected.");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Couldn't update."); }
  };

  if (loading) return <LoadingState label="Loading connectors…" />;

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div>
        <div className="kaelra-kicker">Kaelra’s skills</div>
        <h1 className="font-heading text-2xl">Connected Accounts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          v0 uses realistic demo data. Each connector is built to swap in real OAuth next.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {accounts.map((a) => {
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
  );
}
