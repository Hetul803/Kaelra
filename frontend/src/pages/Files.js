import React, { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { GlassCard, EmptyState, LoadingState, StatusPill } from "../components/Bits";
import { KaelraOrb } from "../components/KaelraOrb";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import { FileText, UploadCloud, Star, Trash2, MessageCircleQuestion, CalendarClock, Users, CheckSquare } from "lucide-react";

export default function Files() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [askFile, setAskFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [asking, setAsking] = useState(false);
  const inputRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { const { data } = await api.get("/files"); setFiles(data); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/files/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`Kaelra read ${data.file.name}.` + (data.actions_prepared ? ` Prepared ${data.actions_prepared} reminder(s).` : ""));
      if (data.actions_prepared) triggerKaelraRefresh();
      load();
    } catch (err) {
      toast.error("Upload failed.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const toggleImportant = async (f) => {
    await api.put(`/files/${f.id}/important`, null, { params: { important: !f.important } });
    load();
  };
  const remove = async (f) => { await api.delete(`/files/${f.id}`); toast.success("File removed."); load(); };

  const openAsk = (f) => { setAskFile(f); setQuestion(""); setAnswer(""); };
  const ask = async () => {
    if (!question.trim()) return;
    setAsking(true); setAnswer("");
    try {
      const { data } = await api.post(`/files/${askFile.id}/ask`, { question });
      setAnswer(data.answer);
    } catch (e) { toast.error("Kaelra couldn't answer that."); }
    finally { setAsking(false); }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="kaelra-kicker">Kaelra reads & remembers</div>
          <h1 className="font-heading text-2xl">Files</h1>
          <p className="mt-1 text-sm text-muted-foreground">Upload a PDF, doc or text file — she’ll summarize it and pull out deadlines.</p>
        </div>
        <input ref={inputRef} type="file" hidden onChange={onUpload} accept=".pdf,.docx,.txt,.md,.csv,.json" data-testid="file-input" />
        <Button onClick={() => inputRef.current?.click()} disabled={uploading} className="gap-1.5" data-testid="file-upload-button">
          <UploadCloud size={16} /> {uploading ? "Reading…" : "Upload file"}
        </Button>
      </div>

      {uploading && (
        <GlassCard className="rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <KaelraOrb size={40} state="thinking" />
            <span className="text-sm text-muted-foreground font-mono-k">Kaelra is reading your file…</span>
          </div>
        </GlassCard>
      )}

      {loading ? (
        <LoadingState label="Loading files…" />
      ) : files.length === 0 && !uploading ? (
        <EmptyState icon={FileText} title="No files yet"
          hint="Upload a syllabus, resume or contract and ask Kaelra to explain it."
          action={<Button onClick={() => inputRef.current?.click()} className="gap-1.5"><UploadCloud size={16} /> Upload file</Button>} />
      ) : (
        <div className="space-y-3">
          {files.map((f) => (
            <GlassCard key={f.id} className="rounded-2xl p-4">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]"><FileText size={18} /></span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="truncate font-heading">{f.name}</h4>
                    {f.important && <StatusPill tone="amber"><Star size={11} /> important</StatusPill>}
                  </div>
                  {f.summary ? (
                    <>
                      <p className="mt-1 text-sm text-foreground/90">{f.summary.summary}</p>
                      <div className="mt-3 grid gap-3 sm:grid-cols-3">
                        {f.summary.deadlines?.length > 0 && (
                          <div>
                            <div className="mb-1 flex items-center gap-1 kaelra-kicker"><CalendarClock size={12} /> Deadlines</div>
                            <ul className="space-y-1 text-xs text-muted-foreground">
                              {f.summary.deadlines.map((d, i) => <li key={i}>{d.title} — <span className="text-foreground/80">{d.date}</span></li>)}
                            </ul>
                          </div>
                        )}
                        {f.summary.people?.length > 0 && (
                          <div>
                            <div className="mb-1 flex items-center gap-1 kaelra-kicker"><Users size={12} /> People</div>
                            <ul className="space-y-1 text-xs text-muted-foreground">{f.summary.people.map((p, i) => <li key={i}>{p}</li>)}</ul>
                          </div>
                        )}
                        {f.summary.action_items?.length > 0 && (
                          <div>
                            <div className="mb-1 flex items-center gap-1 kaelra-kicker"><CheckSquare size={12} /> Action items</div>
                            <ul className="space-y-1 text-xs text-muted-foreground">{f.summary.action_items.map((a, i) => <li key={i}>{a}</li>)}</ul>
                          </div>
                        )}
                      </div>
                    </>
                  ) : <p className="mt-1 text-sm text-muted-foreground">No summary available.</p>}
                  <div className="mt-3 flex gap-1">
                    <Button size="sm" variant="ghost" className="h-8 gap-1 text-xs" onClick={() => openAsk(f)} data-testid="file-ask-button"><MessageCircleQuestion size={13} /> Ask</Button>
                    <Button size="sm" variant="ghost" className="h-8 gap-1 text-xs" onClick={() => toggleImportant(f)}><Star size={13} /> {f.important ? "Unstar" : "Star"}</Button>
                    <Button size="sm" variant="ghost" className="h-8 gap-1 text-xs text-[rgb(254,202,202)]" onClick={() => remove(f)}><Trash2 size={13} /> Delete</Button>
                  </div>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <Dialog open={!!askFile} onOpenChange={(o) => !o && setAskFile(null)}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader><DialogTitle className="truncate">Ask about {askFile?.name}</DialogTitle></DialogHeader>
          <div className="flex gap-2">
            <Input value={question} onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask()}
              placeholder="What’s the late policy?" className="bg-white/5 border-white/10" data-testid="file-ask-input" />
            <Button onClick={ask} disabled={asking} data-testid="file-ask-submit">{asking ? "…" : "Ask"}</Button>
          </div>
          {asking && <p className="text-sm text-muted-foreground font-mono-k">Kaelra is reading…</p>}
          {answer && <div className="glass rounded-xl p-3 text-sm leading-relaxed whitespace-pre-line">{answer}</div>}
        </DialogContent>
      </Dialog>
    </div>
  );
}
