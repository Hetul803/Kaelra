import React, { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import { triggerKaelraRefresh } from "../components/AppShell";
import { ActionCard } from "../components/ActionCard";
import { EmptyState, LoadingState } from "../components/Bits";
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs";
import { ListChecks } from "lucide-react";

const TABS = [
  { id: "pending", label: "Pending" },
  { id: "approved", label: "Approved" },
  { id: "snoozed", label: "Snoozed" },
  { id: "rejected", label: "Rejected" },
  { id: "all", label: "All" },
];

export default function ActionQueue() {
  const [status, setStatus] = useState("pending");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (s) => {
    setLoading(true);
    try {
      const { data } = await api.get("/actions", { params: { status: s } });
      setItems(data);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(status); }, [status, load]);

  const updateAction = async (id, payload) => {
    await api.put(`/actions/${id}`, payload);
    await load(status);
    triggerKaelraRefresh();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <div className="kaelra-kicker">Everything Kaelra prepared</div>
        <h1 className="font-heading text-2xl">Action Queue</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          She prepares; you approve. Sensitive actions never run without your go-ahead.
        </p>
      </div>

      <Tabs value={status} onValueChange={setStatus} data-testid="queue-filter-tabs">
        <TabsList className="bg-white/5">
          {TABS.map((t) => (
            <TabsTrigger key={t.id} value={t.id} data-testid={`queue-tab-${t.id}`}>{t.label}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {loading ? (
        <LoadingState label="Loading your actions…" />
      ) : items.length === 0 ? (
        <EmptyState icon={ListChecks} title="Nothing here right now"
          hint="When Kaelra prepares something useful, it lands here for your approval." />
      ) : (
        <div className="space-y-3">
          {items.map((a) => <ActionCard key={a.id} action={a} onUpdate={updateAction} />)}
        </div>
      )}
    </div>
  );
}
