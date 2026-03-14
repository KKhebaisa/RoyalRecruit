import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Crown, Server, LogOut, ExternalLink, AlertCircle } from "lucide-react";
import { useAuthStore } from "../lib/store";
import { authAPI } from "../lib/api";

interface Guild { id: string; name: string; icon: string | null; }

export default function ServersPage() {
  const user   = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const router = useRouter();
  const [guilds, setGuilds]   = useState<Guild[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    if (!user) { router.push("/"); return; }
    authAPI.guilds()
      .then((r) => setGuilds(r.data))
      .catch(() => setError("Failed to load servers. Please try again."))
      .finally(() => setLoading(false));
  }, [user]);

  const BOT_INVITE = `https://discord.com/api/oauth2/authorize?client_id=${process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID}&permissions=268438544&scope=bot%20applications.commands`;

  return (
    <>
      <Head><title>Select Server – RoyalRecruit</title></Head>
      <div className="min-h-screen" style={{ background: "var(--bg-primary)" }}>
        <nav className="border-b h-14 flex items-center px-6 justify-between" style={{ borderColor: "var(--border)", background: "var(--bg-surface)" }}>
          <div className="flex items-center gap-2">
            <Crown className="w-5 h-5" style={{ color: "var(--crown)" }} />
            <span className="font-display text-lg font-semibold gradient-text">RoyalRecruit</span>
          </div>
          <div className="flex items-center gap-3">
            {user && <span className="text-sm" style={{ color: "var(--text-muted)" }}>{user.username}</span>}
            <button onClick={() => { logout(); router.push("/"); }} className="btn-ghost flex items-center gap-2 py-2 px-3 text-sm">
              <LogOut className="w-4 h-4" /> Logout
            </button>
          </div>
        </nav>
        <div className="max-w-4xl mx-auto px-6 py-12">
          <h1 className="font-display text-4xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Select a Server</h1>
          <p className="mb-8" style={{ color: "var(--text-muted)" }}>Choose a server where you have administrator permissions.</p>
          <div className="crown-divider mb-8" />
          {loading && (
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="glass-card p-5 animate-pulse">
                  <div className="w-12 h-12 rounded-full mb-3" style={{ background: "var(--bg-elevated)" }} />
                  <div className="h-4 rounded w-3/4" style={{ background: "var(--bg-elevated)" }} />
                </div>
              ))}
            </div>
          )}
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-lg" style={{ background: "rgba(237,66,69,0.1)", border: "1px solid rgba(237,66,69,0.2)" }}>
              <AlertCircle className="w-5 h-5 text-red-400" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          {!loading && !error && guilds.length === 0 && (
            <div className="text-center py-16">
              <Server className="w-12 h-12 mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
              <h3 className="font-semibold mb-2" style={{ color: "var(--text-primary)" }}>No servers found</h3>
              <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>Invite the bot to your server to get started.</p>
              <a href={BOT_INVITE} target="_blank" rel="noreferrer" className="btn-primary inline-flex items-center gap-2">
                <ExternalLink className="w-4 h-4" /> Invite Bot
              </a>
            </div>
          )}
          {!loading && guilds.length > 0 && (
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              {guilds.map((g) => (
                <button key={g.id} onClick={() => router.push(`/dashboard/${g.id}`)}
                  className="glass-card p-5 text-left"
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--crown)")}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
                  style={{ transition: "border-color 0.2s" }}>
                  <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 overflow-hidden" style={{ background: "rgba(201,151,59,0.12)" }}>
                    {g.icon
                      ? <img src={`https://cdn.discordapp.com/icons/${g.id}/${g.icon}.webp?size=64`} alt={g.name} className="w-full h-full object-cover rounded-full" />
                      : <Server className="w-6 h-6" style={{ color: "var(--crown)" }} />}
                  </div>
                  <p className="font-medium text-sm truncate" style={{ color: "var(--text-primary)" }}>{g.name}</p>
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Configure →</p>
                </button>
              ))}
              <a href={BOT_INVITE} target="_blank" rel="noreferrer"
                className="glass-card p-5 flex flex-col items-center justify-center" style={{ borderStyle: "dashed" }}>
                <span className="text-3xl mb-2" style={{ color: "var(--crown)" }}>+</span>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>Add server</p>
              </a>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
