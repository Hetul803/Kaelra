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
import { Brain, Plus, Star, Pencil, Trash2, Clock } from "lucide-react";

const emptyForm = { category: "Personal facts", content: "", important: false, temporary: false };

export default function Memory() {
  const [categories, setCategories] = useState([]);
  const [memories, setMemories] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);

  const load = useCallback(async (cat) => {
    setLoading(true);
    try {
      const { data } = await api.get("/memories", { params: { category: cat } });
      setCategories(data.categories);
      setMemories(data.memories);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(filter); }, [filter, load]);

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
          <p className="mt-1 text-sm text-muted-foreground">Everything here shapes how she helps you. You’re in control.</p>
        </div>
        <Button onClick={openAdd} className="gap-1.5" data-testid="memory-add-button"><Plus size={16} /> Add memory</Button>
      </div>

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
