import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Plus, Trash2, Layout, Save, X, Hash } from "lucide-react";
import DashboardLayout from "../../../components/dashboard/Layout";
import { panelsAPI, ticketsAPI, applicationsAPI } from "../../../lib/api";

interface Panel { id: number; panel_type: string; title: string; description: string; channel_id: string; message_id: string | null; ticket_types: any[]; application_types: any[]; }

export default function PanelsPage() {
  const router  = useRouter();
  const guildId = router.query.guildId as string;
  const [panels, setPanels]     = useState<Panel[]>([]);
  const [ttypes, setTtypes]     = useState<any[]>([]);
  const [atypes, setAtypes]     = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [form, setForm]         = useState({ panel_type: "ticket", title: "", description: "", channel_id: "", ticket_type_ids: [] as number[], application_type_ids: [] as number[] });

  useEffect(() => {
    if (!guildId) return;
    Promise.all([panelsAPI.list(guildId), ticketsAPI.listTypes(guildId), applicationsAPI.listTypes(guildId)])
      .then(([p, t, a]) => { setPanels(p.data); setTtypes(t.data); setAtypes(a.data); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [guildId]);

  async function handleCreate() {
    setSaving(true);
    try {
      const r = await panelsAPI.create(guildId, form);
      const newPanel = { ...form, id: r.data.id, ticket_types: ttypes.filter((t) => form.ticket_type_ids.includes(t.id)), application_types: atypes.filter((a) => form.application_type_ids.includes(a.id)), message_id: null };
      setPanels((p) => [...p, newPanel as Panel]);
      setShowForm(false);
      setForm({ panel_type: "ticket", title: "", description: "", channel_id: "", ticket_type_ids: [], application_type_ids: [] });
    } catch (e) { console.error(e); }
    setSaving(false);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this panel?")) return;
    await panelsAPI.delete(guildId, id);
    setPanels((p) => p.filter((x) => x.id !== id));
  }

  function toggleId(arr: number[], id: number): number[] {
    return arr.includes(id) ? arr.filter((x) => x !== id) : [...arr, id];
  }

  return (
    <>
      <Head><title>Panels – RoyalRecruit</title></Head>
      <DashboardLayout guildId={guildId}>
        <div className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-display text-3xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Panels</h1>
              <p style={{ color: "var(--text-muted)" }}>Create embed panels with buttons to deploy in your channels</p>
            </div>
            <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> New Panel
            </button>
          </div>
          <div className="crown-divider mb-8" />

          {showForm && (
            <div className="glass-card p-6 mb-8">
              <h2 className="font-semibold mb-5" style={{ color: "var(--text-primary)" }}>Create Panel</h2>
              <div className="grid md:grid-cols-2 gap-4 mb-5">
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Panel Type</label>
                  <select className="input-base" value={form.panel_type} onChange={(e) => setForm((p) => ({ ...p, panel_type: e.target.value }))}>
                    <option value="ticket">Ticket</option>
                    <option value="application">Application</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Channel ID (for reference)</label>
                  <input className="input-base" placeholder="Discord channel ID" value={form.channel_id}
                    onChange={(e) => setForm((p) => ({ ...p, channel_id: e.target.value }))} />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Title *</label>
                  <input className="input-base" placeholder="e.g. Alliance Recruitment" value={form.title}
                    onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Description</label>
                  <textarea className="input-base" rows={2} placeholder="Panel description…" value={form.description}
                    onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))} />
                </div>
              </div>

              {form.panel_type === "ticket" && ttypes.length > 0 && (
                <div className="mb-5">
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>Ticket Types (buttons)</label>
                  <div className="flex flex-wrap gap-2">
                    {ttypes.map((t) => {
                      const sel = form.ticket_type_ids.includes(t.id);
                      return (
                        <button key={t.id} onClick={() => setForm((p) => ({ ...p, ticket_type_ids: toggleId(p.ticket_type_ids, t.id) }))}
                          className="px-3 py-1.5 rounded-lg text-sm transition-all"
                          style={{ background: sel ? "rgba(201,151,59,0.15)" : "transparent", border: `1px solid ${sel ? "var(--crown)" : "var(--border)"}`, color: sel ? "var(--crown)" : "var(--text-muted)" }}>
                          {t.ticket_name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {form.panel_type === "application" && atypes.length > 0 && (
                <div className="mb-5">
                  <label className="block text-xs mb-2 font-medium" style={{ color: "var(--text-muted)" }}>Application Types (buttons)</label>
                  <div className="flex flex-wrap gap-2">
                    {atypes.map((a) => {
                      const sel = form.application_type_ids.includes(a.id);
                      return (
                        <button key={a.id} onClick={() => setForm((p) => ({ ...p, application_type_ids: toggleId(p.application_type_ids, a.id) }))}
                          className="px-3 py-1.5 rounded-lg text-sm transition-all"
                          style={{ background: sel ? "rgba(201,151,59,0.15)" : "transparent", border: `1px solid ${sel ? "var(--crown)" : "var(--border)"}`, color: sel ? "var(--crown)" : "var(--text-muted)" }}>
                          {a.application_name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button onClick={handleCreate} disabled={saving} className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" /> {saving ? "Saving…" : "Create Panel"}
                </button>
                <button onClick={() => setShowForm(false)} className="btn-ghost flex items-center gap-2">
                  <X className="w-4 h-4" /> Cancel
                </button>
              </div>
            </div>
          )}

          {loading
            ? <p style={{ color: "var(--text-muted)" }}>Loading…</p>
            : panels.length === 0
              ? <div className="text-center py-16 glass-card">
                  <Layout className="w-10 h-10 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
                  <p style={{ color: "var(--text-muted)" }}>No panels yet. Create one to deploy buttons in Discord.</p>
                </div>
              : <div className="space-y-4">
                  {panels.map((p) => (
                    <div key={p.id} className="glass-card p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium" style={{ color: "var(--text-primary)" }}>{p.title}</p>
                            <span className="badge" style={{ background: "rgba(88,101,242,0.12)", color: "#5865F2", border: "1px solid rgba(88,101,242,0.25)" }}>{p.panel_type}</span>
                          </div>
                          {p.description && <p className="text-sm" style={{ color: "var(--text-muted)" }}>{p.description}</p>}
                        </div>
                        <button onClick={() => handleDelete(p.id)} className="p-1.5 rounded" style={{ color: "#ED4245" }}>
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {[...(p.ticket_types ?? []), ...(p.application_types ?? [])].map((t: any) => (
                          <span key={t.id} className="text-xs px-2.5 py-1 rounded-lg" style={{ background: "rgba(201,151,59,0.1)", color: "var(--crown)", border: "1px solid rgba(201,151,59,0.2)" }}>
                            {t.ticket_name ?? t.application_name}
                          </span>
                        ))}
                      </div>
                      <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
                        Deploy with: <code className="font-mono">/sendpanel {p.id}</code>
                        {p.message_id && <span className="ml-3">Message ID: {p.message_id}</span>}
                      </p>
                    </div>
                  ))}
                </div>
          }
        </div>
      </DashboardLayout>
    </>
  );
}
