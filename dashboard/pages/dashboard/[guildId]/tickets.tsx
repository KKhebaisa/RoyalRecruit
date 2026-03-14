import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Plus, Trash2, Edit2, Ticket, Save, X } from "lucide-react";
import DashboardLayout from "../../../components/dashboard/Layout";
import { ticketsAPI } from "../../../lib/api";

interface TicketType { id: number; ticket_name: string; ticket_description: string; ticket_category_id: string; staff_role_id: string; panel_message: string; button_label: string; }

const EMPTY: Partial<TicketType> = { ticket_name: "", ticket_description: "", ticket_category_id: "", staff_role_id: "", panel_message: "", button_label: "" };

export default function TicketsPage() {
  const router  = useRouter();
  const guildId = router.query.guildId as string;
  const [types, setTypes]       = useState<TicketType[]>([]);
  const [editing, setEditing]   = useState<Partial<TicketType> | null>(null);
  const [isNew, setIsNew]       = useState(false);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [tickets, setTickets]   = useState<any[]>([]);

  useEffect(() => {
    if (!guildId) return;
    Promise.all([ticketsAPI.listTypes(guildId), ticketsAPI.listTickets(guildId)])
      .then(([t, tl]) => { setTypes(t.data); setTickets(tl.data); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [guildId]);

  async function handleSave() {
    if (!editing) return;
    setSaving(true);
    try {
      if (isNew) {
        const r = await ticketsAPI.createType(guildId, editing);
        setTypes((p) => [...p, r.data]);
      } else {
        await ticketsAPI.updateType(guildId, editing.id!, editing);
        setTypes((p) => p.map((t) => t.id === editing.id ? { ...t, ...editing } as TicketType : t));
      }
      setEditing(null);
    } catch (e) { console.error(e); }
    setSaving(false);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this ticket type?")) return;
    await ticketsAPI.deleteType(guildId, id);
    setTypes((p) => p.filter((t) => t.id !== id));
  }

  return (
    <>
      <Head><title>Tickets – RoyalRecruit</title></Head>
      <DashboardLayout guildId={guildId}>
        <div className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-display text-3xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Ticket Types</h1>
              <p style={{ color: "var(--text-muted)" }}>Configure ticket categories for your server</p>
            </div>
            <button onClick={() => { setEditing({ ...EMPTY }); setIsNew(true); }} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> New Type
            </button>
          </div>
          <div className="crown-divider mb-8" />

          {/* Editor */}
          {editing && (
            <div className="glass-card p-6 mb-8">
              <h2 className="font-semibold mb-5" style={{ color: "var(--text-primary)" }}>{isNew ? "Create Ticket Type" : "Edit Ticket Type"}</h2>
              <div className="grid md:grid-cols-2 gap-4">
                {[
                  { key: "ticket_name", label: "Name *", placeholder: "e.g. Recruitment" },
                  { key: "button_label", label: "Button Label", placeholder: "e.g. Open Ticket" },
                  { key: "ticket_category_id", label: "Category Channel ID", placeholder: "Discord channel ID" },
                  { key: "staff_role_id", label: "Staff Role ID", placeholder: "Discord role ID" },
                ].map((f) => (
                  <div key={f.key}>
                    <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>{f.label}</label>
                    <input className="input-base" placeholder={f.placeholder} value={(editing as any)[f.key] ?? ""}
                      onChange={(e) => setEditing((p) => ({ ...p, [f.key]: e.target.value }))} />
                  </div>
                ))}
                <div className="md:col-span-2">
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Description</label>
                  <textarea className="input-base" rows={2} placeholder="Short description of this ticket type"
                    value={editing.ticket_description ?? ""}
                    onChange={(e) => setEditing((p) => ({ ...p, ticket_description: e.target.value }))} />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Welcome Message</label>
                  <textarea className="input-base" rows={3} placeholder="Message shown when ticket is opened"
                    value={editing.panel_message ?? ""}
                    onChange={(e) => setEditing((p) => ({ ...p, panel_message: e.target.value }))} />
                </div>
              </div>
              <div className="flex gap-3 mt-5">
                <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" /> {saving ? "Saving…" : "Save"}
                </button>
                <button onClick={() => { setEditing(null); setIsNew(false); }} className="btn-ghost flex items-center gap-2">
                  <X className="w-4 h-4" /> Cancel
                </button>
              </div>
            </div>
          )}

          {/* Types list */}
          {loading
            ? <p style={{ color: "var(--text-muted)" }}>Loading…</p>
            : types.length === 0
              ? <div className="text-center py-16 glass-card">
                  <Ticket className="w-10 h-10 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
                  <p style={{ color: "var(--text-muted)" }}>No ticket types yet. Create one above.</p>
                </div>
              : <div className="space-y-3 mb-10">
                  {types.map((t) => (
                    <div key={t.id} className="glass-card p-4 flex items-center justify-between">
                      <div>
                        <p className="font-medium" style={{ color: "var(--text-primary)" }}>{t.ticket_name}</p>
                        {t.ticket_description && <p className="text-sm mt-0.5" style={{ color: "var(--text-muted)" }}>{t.ticket_description}</p>}
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => { setEditing({ ...t }); setIsNew(false); }} className="btn-ghost py-1.5 px-3 flex items-center gap-1 text-xs">
                          <Edit2 className="w-3 h-3" /> Edit
                        </button>
                        <button onClick={() => handleDelete(t.id)} className="py-1.5 px-3 rounded-lg text-xs flex items-center gap-1 transition-colors"
                          style={{ color: "#ED4245", border: "1px solid rgba(237,66,69,0.25)", background: "rgba(237,66,69,0.06)" }}>
                          <Trash2 className="w-3 h-3" /> Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
          }

          {/* Recent tickets */}
          {tickets.length > 0 && (
            <div className="glass-card p-6">
              <h2 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Recent Tickets</h2>
              <div className="space-y-2">
                {tickets.slice(0, 20).map((t) => (
                  <div key={t.id} className="flex items-center gap-4 text-sm py-2 border-b" style={{ borderColor: "var(--border)" }}>
                    <span className={`badge badge-${t.status}`}>{t.status}</span>
                    <span style={{ color: "var(--text-primary)" }}>#{String(t.serial).padStart(3, "0")} {t.type_name}</span>
                    <span className="ml-auto text-xs" style={{ color: "var(--text-muted)" }}>{t.user}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </DashboardLayout>
    </>
  );
}
