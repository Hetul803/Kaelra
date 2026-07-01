import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { GlassCard, EmptyState, LoadingState, StatusPill } from "../components/Bits";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Switch } from "../components/ui/switch";
import { Label } from "../components/ui/label";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "../components/ui/alert-dialog";
import { Brain, Plus, Star, Pencil, Trash2, Clock, Sparkles, RefreshCw, Layers } from "lucide-react";

const emptyForm = { category: "Personal facts", content: "", important: false, temporary: false };

export default function Memory() {
  const [categories, setCategories] = useState([]);
  const [memories, setMemories] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);
  const [insights, setInsights] = useState(null);
  const [consolidating, setConsolidating] = useState(false);

  const loadInsights = useCallback(async () => {
    try { const { data } = await api.get("/memory/insights"); setInsights(data); } catch (e) { /* ignore */ }
  }, []);

  const load = useCallback(async (cat) => {
    setLoading(true);
    try {
      const { data } = await api.get("/memories", { params: { category: cat } });
      setCategories(data.categories);
      setMemories(data.memories);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(filter); }, [filter, load]);
  useEffect(() => { loadInsights(); }, [loadInsights]);

  const runConsolidate = async () => {
    setConsolidating(true);
    try {
      const { data } = await api.post("/memory/consolidate");
      if (data.consolidated > 0) {
        toast.success(`Kaelra wove ${data.processed} observations into ${data.consolidated} durable ${data.consolidated === 1 ? "memory" : "memories"}.`);
      } else if (data.skipped === "nothing" || data.processed === 0) {
        toast.message("Nothing new to weave in yet.");
      } else {
        toast.message("Kaelra reviewed her recent notes — nothing new to merge.");
      }
      await Promise.all([loadInsights(), load(filter)]);
    } catch (e) { toast.error("Couldn't consolidate right now."); }
    finally { setConsolidating(false); }
  };

  const openAdd = () => { setEditing(null); setForm(emptyForm); setDialogOpen(true); };
  const openEdit = (m) => { setEditing(m); setForm({ category: m.category, content: m.content, important: m.important, temporary: m.temporary }); setDialogOpen(true); };

  const save = async () => {
    if (!form.content.trim()) { toast.error("Add something for Kaelra to remember."); return; }
    try {
      if (editing) await api.put(`/memories/${editing.id}`, form);
      else await api.post("/memories", form);
      toast.success(editing ? "Memory updated." : "Kaelra will remember that.");
      setDialogOpen(false);
      load(filter);
    } catch (e) { toast.error("Couldn't save memory."); }
  };

  const forget = async (m) => {
    await api.delete(`/memories/${m.id}`);
    toast.success("Forgotten.");
    load(filter);
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="kaelra-kicker">What Kaelra knows</div>
          <h1 className="font-heading text-2xl">Memory</h1>
          <p className="mt-1 text-sm text-muted-foreground">One continuous memory that evolves as she learns. You’re always in control.</p>
        </div>
        <Button onClick={openAdd} className="gap-1.5" data-testid="memory-add-button"><Plus size={16} /> Add memory</Button>
      </div>

      {/* Unified continuous memory + consolidation */}
      <GlassCard className="rounded-2xl p-4" data-testid="memory-consolidation-panel">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/5 text-[hsl(var(--primary))]"><Layers size={20} /></span>
            <div>
              <div className="font-heading">One continuous memory</div>
              <p className="mt-0.5 max-w-md text-sm text-muted-foreground">
                Kaelra doesn’t keep separate boxes. Everything she observes flows into one evolving memory — fresh observations are woven into durable, non-redundant knowledge.
              </p>
            </div>
          </div>
          <Button onClick={runConsolidate} disabled={consolidating} className="shrink-0 gap-1.5" data-testid="memory-consolidate-button">
            <RefreshCw size={15} className={consolidating ? "animate-spin" : ""} /> {consolidating ? "Weaving…" : "Consolidate now"}
          </Button>
        </div>
        {insights && (
          <div className="mt-4 grid grid-cols-3 gap-2" data-testid="memory-insights">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
              <div className="font-heading text-xl" data-testid="memory-insight-total">{insights.total}</div>
              <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">Total</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
              <div className="flex items-center justify-center gap-1 font-heading text-xl text-[hsl(var(--primary))]" data-testid="memory-insight-durable">
                <Sparkles size={15} /> {insights.consolidated}
              </div>
              <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">Durable</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
              <div className={`font-heading text-xl ${insights.pending_consolidation > 0 ? "text-[hsl(var(--accent))]" : ""}`} data-testid="memory-insight-pending">{insights.pending_consolidation}</div>
              <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">To weave in</div>
            </div>
          </div>
        )}
      </GlassCard>

      <div className="flex flex-wrap gap-2" data-testid="memory-category-filter">
        {["all", ...categories].map((c) => (
          <button key={c} onClick={() => setFilter(c)}
            className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
              filter === c ? "border-[hsl(var(--primary))] bg-[rgba(45,212,191,0.15)] text-foreground"
                           : "border-white/10 bg-white/5 text-muted-foreground hover:text-foreground"}`}>
            {c === "all" ? "All" : c}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState label="Loading memories…" />
      ) : memories.length === 0 ? (
        <EmptyState icon={Brain} title="No memories in this category yet"
          hint="Tell Kaelra what matters — facts, people, routines, things to watch."
          action={<Button onClick={openAdd} className="gap-1.5"><Plus size={16} /> Add memory</Button>} />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {memories.map((m) => (
            <GlassCard key={m.id} className="rounded-2xl p-4">
              <div className="flex items-start justify-between gap-2">
                <span className="kaelra-kicker">{m.category}</span>
                <div className="flex gap-1">
                  {m.important && <StatusPill tone="amber"><Star size={11} /> important</StatusPill>}
                  {m.temporary && <StatusPill tone="teal"><Clock size={11} /> temporary</StatusPill>}
                </div>
              </div>
              <p className="mt-2 text-sm leading-relaxed">{m.content}</p>
              <div className="mt-3 flex gap-1">
                <Button size="sm" variant="ghost" className="h-8 gap-1 text-xs" onClick={() => openEdit(m)}><Pencil size={13} /> Edit</Button>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button size="sm" variant="ghost" className="h-8 gap-1 text-xs text-[rgb(254,202,202)]" data-testid="memory-forget-button"><Trash2 size={13} /> Forget</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="glass-strong border-white/10">
                    <AlertDialogHeader>
                      <AlertDialogTitle>Forget this memory?</AlertDialogTitle>
                      <AlertDialogDescription>Kaelra will no longer use this. This can’t be undone.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Keep</AlertDialogCancel>
                      <AlertDialogAction onClick={() => forget(m)}>Forget</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader><DialogTitle>{editing ? "Edit memory" : "Add memory"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="mb-1 block">Category</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger className="bg-white/5 border-white/10" data-testid="memory-category-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {categories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="mb-1 block">What should Kaelra remember?</Label>
              <Textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })}
                rows={3} className="bg-white/5 border-white/10" data-testid="memory-content-input" />
            </div>
            <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2">
              <span className="text-sm">Mark as important</span>
              <Switch checked={form.important} onCheckedChange={(v) => setForm({ ...form, important: v })} />
            </div>
            <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2">
              <span className="text-sm">Temporary (forget later)</span>
              <Switch checked={form.temporary} onCheckedChange={(v) => setForm({ ...form, temporary: v })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={save} data-testid="memory-save-button">{editing ? "Save" : "Remember"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
