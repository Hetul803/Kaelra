import React, { useCallback, useEffect, useState } from "react";
import { formatDistanceToNow, parseISO } from "date-fns";
import { toast } from "sonner";
import { api } from "../lib/api";
import { locationSupported, isLocationEnabled, enableLocation, disableLocation } from "../lib/location";
import { GlassCard, SectionTitle, StatusPill, LoadingState } from "../components/Bits";
import { Button } from "../components/ui/button";
import { MapPin, Route, Navigation, Clock, ShieldCheck, Sparkles } from "lucide-react";

function rel(iso) {
  try { return formatDistanceToNow(parseISO(iso), { addSuffix: true }); } catch (e) { return ""; }
}

export default function Timeline() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState(isLocationEnabled());
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/location/timeline");
    setData(data);
  }, []);

  useEffect(() => { (async () => { try { await load(); } finally { setLoading(false); } })(); }, [load]);

  const toggle = async () => {
    setBusy(true);
    try {
      if (enabled) { disableLocation(); setEnabled(false); toast.success("Location tracking paused."); }
      else { await enableLocation(); setEnabled(true); toast.success("Kaelra is learning your places."); await load(); }
    } catch (e) {
      if (e?.message === "denied") toast.error("Location permission was blocked.");
      else if (e?.message === "unsupported") toast.message("This device doesn't support location.");
      else toast.error("Couldn't enable location.");
    } finally { setBusy(false); }
  };

  if (loading) return <LoadingState label="Loading your timeline…" />;

  const places = data?.places || [];
  const frequent = data?.frequent || [];

  return (
    <div className="mx-auto max-w-4xl space-y-5" data-testid="timeline-root">
      <div>
        <div className="kaelra-kicker">Where you go</div>
        <h1 className="font-heading text-2xl">Your Timeline</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Kaelra quietly learns the places that matter to you and connects them with your day — all on your account.
        </p>
      </div>

      <GlassCard className="rounded-2xl p-5" data-testid="timeline-enable-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]"><Navigation size={20} /></span>
            <div>
              <div className="flex items-center gap-2">
                <div className="font-heading">Location learning</div>
                <StatusPill tone={enabled ? "green" : "default"}>{enabled ? "On" : "Off"}</StatusPill>
              </div>
              <p className="mt-0.5 text-sm text-muted-foreground">
                {locationSupported() ? "Kaelra logs where you spend time and builds a private timeline." : "Location isn't available on this device."}
              </p>
            </div>
          </div>
          <Button onClick={toggle} disabled={busy || !locationSupported()} variant={enabled ? "secondary" : "default"} className="gap-1.5 shrink-0" data-testid="timeline-toggle-button">
            <MapPin size={15} /> {enabled ? "Pause" : "Enable location"}
          </Button>
        </div>
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5">
          <ShieldCheck size={15} className="mt-0.5 shrink-0 text-[hsl(var(--primary))]" />
          <p className="text-xs text-muted-foreground">Your location stays on your Kaelra account. You can pause anytime and it never leaves without your approval.</p>
        </div>
      </GlassCard>

      <div className="grid gap-5 lg:grid-cols-2">
        <div data-testid="timeline-frequent">
          <SectionTitle kicker="Learned" title="Frequent places" icon={Sparkles} />
          <GlassCard className="rounded-2xl p-4">
            {frequent.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">Once location is on, your regular places will appear here — and Kaelra will remember them.</p>
            ) : (
              <ul className="space-y-2">
                {frequent.map((p, i) => (
                  <li key={i} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3" data-testid={`timeline-frequent-${i}`}>
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]"><MapPin size={16} /></span>
                    <div className="min-w-0 flex-1"><div className="truncate text-sm">{p.label}</div></div>
                    <StatusPill tone="teal">{p.visits} visits</StatusPill>
                  </li>
                ))}
              </ul>
            )}
          </GlassCard>
        </div>

        <div data-testid="timeline-recent">
          <SectionTitle kicker="History" title="Recent places" icon={Route}
            action={<span className="font-mono-k text-xs text-muted-foreground">{data?.today_points || 0} points today</span>} />
          <GlassCard className="rounded-2xl p-4">
            {places.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No places yet.</p>
            ) : (
              <ol className="relative space-y-3 before:absolute before:left-[5px] before:top-1 before:h-[calc(100%-0.5rem)] before:w-px before:bg-white/10">
                {places.slice(0, 12).map((p) => (
                  <li key={p.id} className="relative pl-6" data-testid="timeline-place">
                    <span className="absolute left-0 top-1.5 h-[11px] w-[11px] rounded-full border-2 border-[hsl(var(--background))] bg-[hsl(var(--primary))]" />
                    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                      <div className="text-sm">{p.label}</div>
                      <div className="mt-1 flex items-center gap-2 font-mono-k text-[11px] text-muted-foreground">
                        <Clock size={11} /> {rel(p.last_seen)} <span aria-hidden>·</span> {p.visits} visits
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
