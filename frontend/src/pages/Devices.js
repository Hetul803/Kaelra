import React, { useCallback, useEffect, useState } from "react";
import { formatDistanceToNow, parseISO } from "date-fns";
import { api } from "../lib/api";
import { getDeviceId } from "../lib/device";
import { GlassCard, LoadingState, StatusPill } from "../components/Bits";
import { KaelraOrb } from "../components/KaelraOrb";
import { Laptop, Smartphone, Tablet, Mic, Bell, MonitorSmartphone } from "lucide-react";

const ICON = { laptop: Laptop, phone: Smartphone, tablet: Tablet };

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const current = getDeviceId();

  const load = useCallback(async () => {
    setLoading(true);
    try { const { data } = await api.get("/devices"); setDevices(data); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingState label="Finding your devices…" />;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <div className="kaelra-kicker">Synced everywhere</div>
        <h1 className="font-heading text-2xl">Devices</h1>
        <p className="mt-1 text-sm text-muted-foreground">Kaelra stays with you across phone and laptop. Pick up right where you left off.</p>
      </div>

      <GlassCard className="rounded-2xl p-4">
        <div className="flex items-center gap-3">
          <KaelraOrb size={44} state="idle" />
          <div className="flex-1">
            <div className="text-sm">Kaelra is synced on this device</div>
            <div className="text-xs text-muted-foreground font-mono-k">{devices.length} device{devices.length !== 1 ? "s" : ""} active</div>
          </div>
          <span className="h-2.5 w-2.5 rounded-full bg-[hsl(var(--primary))] animate-pulse" />
        </div>
      </GlassCard>

      <div className="grid gap-3 sm:grid-cols-2">
        {devices.map((d) => {
          const Icon = ICON[d.kind] || MonitorSmartphone;
          const isCurrent = d.device_id === current;
          return (
            <GlassCard key={d.id} className={`rounded-2xl p-4 ${isCurrent ? "border-[hsl(var(--primary))]/40" : ""}`} data-testid="device-card">
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]"><Icon size={20} /></span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-heading truncate">{d.name}</span>
                    {isCurrent && <StatusPill tone="teal">This device</StatusPill>}
                  </div>
                  <div className="text-xs text-muted-foreground font-mono-k">
                    Active {d.last_active ? formatDistanceToNow(parseISO(d.last_active), { addSuffix: true }) : "recently"}
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <StatusPill tone={d.voice_enabled ? "teal" : "default"}><Mic size={12} /> Voice {d.voice_enabled ? "on" : "off"}</StatusPill>
                <StatusPill tone={d.notifications_enabled ? "green" : "default"}><Bell size={12} /> Alerts {d.notifications_enabled ? "on" : "off"}</StatusPill>
              </div>
              {!isCurrent && (
                <p className="mt-3 text-xs text-muted-foreground">Continue on {d.kind === "phone" ? "your phone" : "this device"} — your conversations and queue stay in sync.</p>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
