import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Ticket, ClipboardList, Layout, Activity } from "lucide-react";
import DashboardLayout from "../../../components/dashboard/Layout";
import { guildsAPI, ticketsAPI, applicationsAPI, logsAPI } from "../../../lib/api";

export default function GuildDashboard() {
  const router  = useRouter();
  const guildId = router.query.guildId as string;
  const [guild, setGuild]     = useState<any>(null);
  const [stats, setStats]     = useState({ tickets: 0, applications: 0, panels: 0 });
  const [logs, setLogs]       = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!guildId) return;
    Promise.all([guildsAPI.get(guildId), ticketsAPI.listTickets(guildId), applicationsAPI.listApplications(guildId), logsAPI.list(guildId)])
      .then(([g, t, a, l]) => {
        setGuild(g.data);
        setStats({ tickets: t.data.length, applications: a.data.length, panels: 0 });
        setLogs(l.data.slice(0, 10));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [guildId]);

  const ICONS: Record<string, string> = { ticket_opened: "🎫", ticket_closed: "🔒", application_submitted: "📋", application_approved: "✅", application_rejected: "❌" };

  return (
    <>
      <Head><title>{guild?.name ?? "Dashboard"} – RoyalRecruit</title></Head>
      <DashboardLayout guildId={guildId} guildName={guild?.name}>
        <div className="p-8">
          <div className="mb-8">
            <h1 className="font-display text-3xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
              {loading ? "Loading…" : guild?.name ?? "Dashboard"}
            </h1>
            <p style={{ color: "var(--text-muted)" }}>Server overview</p>
          </div>
          <div className="crown-divider mb-8" />
          <div className="grid sm:grid-cols-3 gap-5 mb-10">
            {[
              { label: "Total Tickets", value: stats.tickets, icon: <Ticket className="w-5 h-5" />, color: "#5865F2" },
              { label: "Applications", value: stats.applications, icon: <ClipboardList className="w-5 h-5" />, color: "#57F287" },
              { label: "Panels Active", value: stats.panels, icon: <Layout className="w-5 h-5" />, color: "var(--crown)" },
            ].map((s) => (
              <div key={s.label} className="glass-card p-5">
                <div className="w-9 h-9 rounded-lg flex items-center justify-center mb-3" style={{ background: `${s.color}1a`, color: s.color }}>{s.icon}</div>
                <p className="font-display text-3xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>{loading ? "—" : s.value}</p>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>{s.label}</p>
              </div>
            ))}
          </div>
          <div className="glass-card p-6">
            <div className="flex items-center gap-2 mb-5">
              <Activity className="w-4 h-4" style={{ color: "var(--crown)" }} />
              <h2 className="font-semibold" style={{ color: "var(--text-primary)" }}>Recent Activity</h2>
            </div>
            {logs.length === 0
              ? <p className="text-sm text-center py-6" style={{ color: "var(--text-muted)" }}>No activity yet.</p>
              : <div className="space-y-3">
                  {logs.map((log) => (
                    <div key={log.id} className="flex items-center gap-3 text-sm">
                      <span>{ICONS[log.event_type] ?? "📌"}</span>
                      <span className="flex-1" style={{ color: "var(--text-primary)" }}>{log.event_type.replace(/_/g, " ")}</span>
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
            }
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}
