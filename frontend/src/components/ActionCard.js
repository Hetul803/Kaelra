import React, { useState } from "react";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { StatusPill } from "./Bits";
import { actionMeta } from "./actionMeta";
import { ShieldAlert, Check, X, Pencil, Clock } from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";

const STATUS_TONE = {
  pending: "teal", approved: "green", rejected: "red", snoozed: "amber", completed: "green",
};

export function ActionCard({ action, onUpdate, compact = false }) {
  const meta = actionMeta(action.type);
  const Icon = meta.icon;
  const [editOpen, setEditOpen] = useState(false);
  const [title, setTitle] = useState(action.title);
  const [what, setWhat] = useState(action.what);
  const [busy, setBusy] = useState(false);

  const act = async (payload, successMsg) => {
    setBusy(true);
    try {
      await onUpdate(action.id, payload);
      if (successMsg) toast.success(successMsg);
    } catch (e) {
      toast.error("Could not update action.");
    } finally {
      setBusy(false);
    }
  };

  const isPending = action.status === "pending";

  return (
    <div className="glass rounded-2xl p-4 kaelra-fade-up" data-testid="queue-action-card">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/5 text-[hsl(var(--primary))]">
          <Icon size={17} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="kaelra-kicker">{meta.label}</span>
            <StatusPill tone={STATUS_TONE[action.status] || "default"} data-testid="action-queue-item-status-badge">
              {action.status}
            </StatusPill>
            {action.sensitive && (
              <StatusPill tone="sensitive"><ShieldAlert size={12} /> Needs approval</StatusPill>
            )}
          </div>
          <h4 className="mt-1 font-heading text-base leading-snug">{action.title}</h4>
          <p className="mt-1 text-sm text-foreground/90">{action.what}</p>
          {action.why && (
            <p className="mt-2 text-xs text-muted-foreground">
              <span className="text-foreground/70">Why:</span> {action.why}
            </p>
          )}
          {action.source && (
            <p className="mt-1 text-xs text-muted-foreground font-mono-k">Source: {action.source}</p>
          )}
          {action.sensitive && isPending && (
            <p className="mt-2 text-xs text-[rgb(254,215,170)]">
              Sensitive action — waiting for your approval. Kaelra won’t act until you say so.
            </p>
          )}

          {isPending && (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button size="sm" disabled={busy} data-testid="action-queue-item-approve-button"
                onClick={() => act({ status: "approved" }, "Approved.")} className="gap-1">
                <Check size={15} /> Approve
              </Button>
              <Button size="sm" variant="secondary" disabled={busy} data-testid="action-queue-item-reject-button"
                onClick={() => act({ status: "rejected" }, "Rejected.")} className="gap-1">
                <X size={15} /> Reject
              </Button>
              {!compact && (
                <>
                  <Button size="sm" variant="ghost" disabled={busy} data-testid="action-queue-item-edit-button"
                    onClick={() => setEditOpen(true)} className="gap-1">
                    <Pencil size={15} /> Edit
                  </Button>
                  <Button size="sm" variant="secondary" disabled={busy} data-testid="action-queue-item-snooze-button"
                    onClick={() => act({ status: "snoozed" }, "Snoozed.")} className="gap-1">
                    <Clock size={15} /> Snooze
                  </Button>
                </>
              )}
            </div>
          )}
          {!isPending && action.status === "snoozed" && (
            <div className="mt-3">
              <Button size="sm" variant="secondary" disabled={busy}
                onClick={() => act({ status: "pending" }, "Back in your queue.")}>Resume</Button>
            </div>
          )}
        </div>
      </div>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="glass-strong border-white/10">
          <DialogHeader><DialogTitle>Edit action</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} className="bg-white/5 border-white/10" data-testid="action-edit-title" />
            <Textarea value={what} onChange={(e) => setWhat(e.target.value)} rows={4} className="bg-white/5 border-white/10" data-testid="action-edit-what" />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setEditOpen(false)}>Cancel</Button>
            <Button onClick={async () => { await act({ title, what }, "Action updated."); setEditOpen(false); }} data-testid="action-edit-save">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
