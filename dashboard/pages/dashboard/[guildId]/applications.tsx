import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Plus, Trash2, Edit2, ClipboardList, Save, X, GripVertical } from "lucide-react";
import DashboardLayout from "../../../components/dashboard/Layout";
import { applicationsAPI } from "../../../lib/api";

interface Question { id?: number; question_text: string; order_index: number; }
interface AppType { id: number; application_name: string; category_id: string; staff_role_id: string; welcome_message: string; completion_message: string; button_label: string; questions: Question[]; }

const EMPTY: Partial<AppType> = { application_name: "", category_id: "", staff_role_id: "", welcome_message: "", completion_message: "", button_label: "", questions: [] };

export default function ApplicationsPage() {
  const router  = useRouter();
  const guildId = router.query.guildId as string;
  const [types, setTypes]       = useState<AppType[]>([]);
  const [editing, setEditing]   = useState<Partial<AppType> | null>(null);
  const [isNew, setIsNew]       = useState(false);
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [apps, setApps]         = useState<any[]>([]);

  useEffect(() => {
    if (!guildId) return;
    Promise.all([applicationsAPI.listTypes(guildId), applicationsAPI.listApplications(guildId)])
      .then(([t, a]) => { setTypes(t.data); setApps(a.data); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [guildId]);

  function addQuestion() {
    setEditing((p) => ({ ...p, questions: [...(p?.questions ?? []), { question_text: "", order_index: (p?.questions?.length ?? 0) }] }));
  }
  function updateQuestion(i: number, text: string) {
    setEditing((p) => { const qs = [...(p?.questions ?? [])]; qs[i] = { ...qs[i], question_text: text }; return { ...p, questions: qs }; });
  }
  function removeQuestion(i: number) {
    setEditing((p) => { const qs = (p?.questions ?? []).filter((_, idx) => idx !== i).map((q, idx) => ({ ...q, order_index: idx })); return { ...p, questions: qs }; });
  }

  async function handleSave() {
    if (!editing) return; setSaving(true);
    try {
      const payload = { ...editing, questions: (editing.questions ?? []).map((q, i) => ({ ...q, order_index: i })) };
      if (isNew) { const r = await applicationsAPI.createType(guildId, payload); setTypes((p) => [...p, r.data]); }
      else { await applicationsAPI.updateType(guildId, editing.id!, payload); setTypes((p) => p.map((t) => t.id === editing.id ? { ...t, ...payload } as AppType : t)); }
      setEditing(null);
    } catch (e) { console.error(e); }
    setSaving(false);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this application type?")) return;
    await applicationsAPI.deleteType(guildId, id);
    setTypes((p) => p.filter((t) => t.id !== id));
  }

  return (
    <>
      <Head><title>Applications – RoyalRecruit</title></Head>
      <DashboardLayout guildId={guildId}>
        <div className="p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="font-display text-3xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Applications</h1>
              <p style={{ color: "var(--text-muted)" }}>Create structured application forms with custom questions</p>
            </div>
            <button onClick={() => { setEditing({ ...EMPTY, questions: [] }); setIsNew(true); }} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> New Application
            </button>
          </div>
          <div className="crown-divider mb-8" />

          {editing && (
            <div className="glass-card p-6 mb-8">
              <h2 className="font-semibold mb-5" style={{ color: "var(--text-primary)" }}>{isNew ? "Create Application Type" : "Edit Application Type"}</h2>
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                {[
                  { key: "application_name", label: "Name *", placeholder: "e.g. KvK Fighter Application" },
                  { key: "button_label", label: "Button Label", placeholder: "e.g. Apply Now" },
                  { key: "category_id", label: "Category Channel ID", placeholder: "Discord channel ID" },
                  { key: "staff_role_id", label: "Staff Role ID", placeholder: "Discord role ID" },
                ].map((f) => (
                  <div key={f.key}>
                    <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>{f.label}</label>
                    <input className="input-base" placeholder={f.placeholder} value={(editing as any)[f.key] ?? ""}
                      onChange={(e) => setEditing((p) => ({ ...p, [f.key]: e.target.value }))} />
                  </div>
                ))}
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Welcome Message</label>
                  <textarea className="input-base" rows={2} value={editing.welcome_message ?? ""}
                    onChange={(e) => setEditing((p) => ({ ...p, welcome_message: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Completion Message</label>
                  <textarea className="input-base" rows={2} value={editing.completion_message ?? ""}
                    onChange={(e) => setEditing((p) => ({ ...p, completion_message: e.target.value }))} />
                </div>
              </div>

              <div className="mb-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>Questions</h3>
                  <button onClick={addQuestion} className="btn-ghost py-1 px-3 text-xs flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add Question
                  </button>
                </div>
                {(editing.questions ?? []).length === 0
                  ? <p className="text-sm text-center py-4" style={{ color: "var(--text-muted)" }}>No questions yet.</p>
                  : (editing.questions ?? []).map((q, i) => (
                      <div key={i} className="flex items-center gap-2 mb-2">
                        <GripVertical className="w-4 h-4 flex-shrink-0" style={{ color: "var(--text-muted)" }} />
                        <span className="text-xs w-5 text-center flex-shrink-0" style={{ color: "var(--text-muted)" }}>{i + 1}</span>
                        <input className="input-base flex-1" placeholder={`Question ${i + 1}`} value={q.question_text}
                          onChange={(e) => updateQuestion(i, e.target.value)} />
                        <button onClick={() => removeQuestion(i)} className="p-1.5 rounded" style={{ color: "#ED4245" }}>
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                }
              </div>

              <div className="flex gap-3">
                <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" /> {saving ? "Saving…" : "Save"}
                </button>
                <button onClick={() => { setEditing(null); setIsNew(false); }} className="btn-ghost flex items-center gap-2">
                  <X className="w-4 h-4" /> Cancel
                </button>
              </div>
            </div>
          )}

          {loading
            ? <p style={{ color: "var(--text-muted)" }}>Loading…</p>
            : types.length === 0
              ? <div className="text-center py-16 glass-card">
                  <ClipboardList className="w-10 h-10 mx-auto mb-3" style={{ color: "var(--text-muted)" }} />
                  <p style={{ color: "var(--text-muted)" }}>No application types yet.</p>
                </div>
              : <div className="space-y-3 mb-10">
                  {types.map((t) => (
                    <div key={t.id} className="glass-card p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium" style={{ color: "var(--text-primary)" }}>{t.application_name}</p>
                        <div className="flex gap-2">
                          <button onClick={() => { setEditing({ ...t }); setIsNew(false); }} className="btn-ghost py-1.5 px-3 flex items-center gap-1 text-xs">
                            <Edit2 className="w-3 h-3" /> Edit
                          </button>
                          <button onClick={() => handleDelete(t.id)} className="py-1.5 px-3 rounded-lg text-xs flex items-center gap-1"
                            style={{ color: "#ED4245", border: "1px solid rgba(237,66,69,0.25)", background: "rgba(237,66,69,0.06)" }}>
                            <Trash2 className="w-3 h-3" /> Delete
                          </button>
                        </div>
                      </div>
                      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{t.questions.length} question{t.questions.length !== 1 ? "s" : ""}</p>
                    </div>
                  ))}
                </div>
          }

          {apps.length > 0 && (
            <div className="glass-card p-6">
              <h2 className="font-semibold mb-4" style={{ color: "var(--text-primary)" }}>Recent Applications</h2>
              <div className="space-y-2">
                {apps.slice(0, 20).map((a) => (
                  <div key={a.id} className="flex items-center gap-4 text-sm py-2 border-b" style={{ borderColor: "var(--border)" }}>
                    <span className={`badge badge-${a.status}`}>{a.status}</span>
                    <span style={{ color: "var(--text-primary)" }}>{a.type_name}</span>
                    <span className="ml-auto text-xs" style={{ color: "var(--text-muted)" }}>{a.user} · {new Date(a.created_at).toLocaleDateString()}</span>
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
