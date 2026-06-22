import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Switch } from "../components/ui/switch";
import { Slider } from "../components/ui/slider";
import {
  Lightbulb, Thermometer, Lock, LockOpen, ShieldAlert, ShieldCheck, Sun, Home,
  Plus, Minus, Sparkles, DoorClosed,
} from "lucide-react";

function DeviceShell({ children, testid }) {
  return <div className="rounded-2xl border border-white/10 bg-white/5 p-4" data-testid={testid}>{children}</div>;
}

export default function SmartHome() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/home");
    setData(data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const setDevice = async (dev, state, { silent } = {}) => {
    try {
      const { data } = await api.put(`/home/devices/${dev.id}`, { state });
      if (data.pending_approval) {
        toast.success(`Kaelra needs your approval to ${state.locked ? "lock" : "unlock"} ${dev.name} — check the Action Queue.`);
        triggerKaelraRefresh();
      } else if (!silent) {
        toast.success(`${dev.name} updated.`);
      }
      await load();
    } catch (e) { toast.error("Couldn't reach that device."); }
  };

  const runMorning = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/home/morning-routine");
      setData(data);
      toast.success("Good morning — lights on, thermostat set.");
    } catch (e) { toast.error("Couldn't run the routine."); }
    finally { setBusy(false); }
  };

  if (loading) return <LoadingState label="Reaching your home…" />;

  const devices = data?.devices || [];
  const routines = data?.routines || [];

  const renderDevice = (d) => {
    const s = d.state || {};
    if (d.kind === "light") {
      return (
        <DeviceShell key={d.id} testid="home-device-light">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <Lightbulb size={18} className={s.on ? "text-[hsl(var(--accent))]" : "text-muted-foreground"} />
              <div>
                <div className="text-sm font-medium">{d.name}</div>
                <div className="text-[11px] text-muted-foreground">{d.room}</div>
              </div>
            </div>
            <Switch checked={!!s.on} onCheckedChange={(v) => setDevice(d, { on: v })} data-testid="home-light-toggle" />
          </div>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-[11px] text-muted-foreground w-14">Brightness</span>
            <Slider value={[s.brightness ?? 50]} min={0} max={100} step={5} disabled={!s.on}
              onValueCommit={(v) => setDevice(d, { brightness: v[0] }, { silent: true })} className="flex-1" data-testid="home-light-brightness" />
            <span className="w-8 text-right text-xs font-mono-k">{s.brightness ?? 0}</span>
          </div>
        </DeviceShell>
      );
    }
    if (d.kind === "thermostat") {
      return (
        <DeviceShell key={d.id} testid="home-device-thermostat">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Thermometer size={18} className="text-[hsl(var(--primary))]" />
              <div>
                <div className="text-sm font-medium">{d.name}</div>
                <div className="text-[11px] text-muted-foreground capitalize">{s.mode} mode</div>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-center gap-4">
            <Button size="icon" variant="secondary" className="h-9 w-9" onClick={() => setDevice(d, { temp: (s.temp ?? 70) - 1 }, { silent: true })} data-testid="home-thermostat-down"><Minus size={16} /></Button>
            <div className="font-heading text-3xl text-[hsl(var(--primary))]">{s.temp ?? "--"}°</div>
            <Button size="icon" variant="secondary" className="h-9 w-9" onClick={() => setDevice(d, { temp: (s.temp ?? 70) + 1 }, { silent: true })} data-testid="home-thermostat-up"><Plus size={16} /></Button>
          </div>
        </DeviceShell>
      );
    }
    if (d.kind === "lock") {
      const locked = !!s.locked;
      return (
        <DeviceShell key={d.id} testid="home-device-lock">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              {locked ? <Lock size={18} className="text-[hsl(var(--primary))]" /> : <LockOpen size={18} className="text-[hsl(var(--accent))]" />}
              <div>
                <div className="text-sm font-medium">{d.name}</div>
                <div className="text-[11px] text-muted-foreground">{locked ? "Locked" : "Unlocked"}</div>
              </div>
            </div>
            <StatusPill tone="sensitive" className="shrink-0">approval</StatusPill>
          </div>
          <Button size="sm" variant="secondary" className="mt-3 w-full gap-1.5"
            onClick={() => setDevice(d, { locked: !locked })} data-testid="home-lock-toggle">
            <DoorClosed size={14} /> {locked ? "Request unlock" : "Request lock"}
          </Button>
        </DeviceShell>
      );
    }
    if (d.kind === "alarm") {
      return (
        <DeviceShell key={d.id} testid="home-device-alarm">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              {s.armed ? <ShieldCheck size={18} className="text-[hsl(var(--primary))]" /> : <ShieldAlert size={18} className="text-muted-foreground" />}
              <div>
                <div className="text-sm font-medium">{d.name}</div>
                <div className="text-[11px] text-muted-foreground">{s.armed ? "Armed" : "Disarmed"}</div>
              </div>
            </div>
            <Switch checked={!!s.armed} onCheckedChange={(v) => setDevice(d, { armed: v })} data-testid="home-alarm-toggle" />
          </div>
        </DeviceShell>
      );
    }
    return null;
  };

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="kaelra-kicker">Home</div>
          <h1 className="font-heading text-2xl">Smart Home</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Simulated for v0 — locks and other sensitive controls always ask for your approval first.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusPill tone="teal">Simulated</StatusPill>
          <Button size="sm" className="gap-1.5" disabled={busy} onClick={runMorning} data-testid="home-morning-routine-button">
            <Sun size={15} /> Run Good Morning
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {devices.map(renderDevice)}
      </div>

      <GlassCard className="rounded-2xl p-4" data-testid="home-routines">
        <SectionTitle kicker="Automations" title="Home routines" icon={Home} />
        <div className="grid gap-2 sm:grid-cols-3">
          {routines.map((r) => (
            <div key={r.id} className="rounded-xl border border-white/10 bg-white/5 p-3" data-testid="home-routine-card">
              <div className="flex items-center justify-between gap-2">
                <span className="font-heading text-sm">{r.name}</span>
                <span className={`h-2 w-2 rounded-full ${r.enabled ? "bg-[hsl(var(--primary))]" : "bg-white/20"}`} />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{r.actions}</p>
            </div>
          ))}
          {routines.length === 0 && <p className="text-sm text-muted-foreground">No routines yet.</p>}
        </div>
      </GlassCard>
    </div>
  );
}
