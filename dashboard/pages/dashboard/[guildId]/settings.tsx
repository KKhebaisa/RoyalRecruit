import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Head from "next/head";
import { Settings, Save } from "lucide-react";
import DashboardLayout from "../../../components/dashboard/Layout";
import { guildsAPI } from "../../../lib/api";

export default function SettingsPage() {
  const router  = useRouter();
  const guildId = router.query.guildId as string;
  const [logChannel, setLogChannel] = useState("");
  const [saving, setSaving]         = useState(false);
  const [saved, setSaved]           = useState(false);

  useEffect(() => {
    if (!guildId) return;
    guildsAPI.get(guildId).then((r) => setLogChannel(r.data.log_channel_id ?? "")).catch(console.error);
  }, [guildId]);

  async function handleSave() {
    setSaving(true);
    try {
      await guildsAPI.updateSettings(guildId, { log_channel_id: logChannel || null });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) { console.error(e); }
    setSaving(false);
  }

  return (
    <>
      <Head><title>Settings – RoyalRecruit</title></Head>
      <DashboardLayout guildId={guildId}>
        <div className="p-8 max-w-2xl">
          <div className="flex items-center gap-3 mb-8">
            <Settings className="w-6 h-6" style={{ color: "var(--crown)" }} />
            <div>
              <h1 className="font-display text-3xl font-semibold" style={{ color: "var(--text-primary)" }}>Settings</h1>
              <p style={{ color: "var(--text-muted)" }}>Server configuration</p>
            </div>
          </div>
          <div className="crown-divider mb-8" />
          <div className="glass-card p-6">
            <h2 className="font-semibold mb-5" style={{ color: "var(--text-primary)" }}>Logging</h2>
            <div className="mb-5">
              <label className="block text-xs mb-1.5 font-medium" style={{ color: "var(--text-muted)" }}>Log Channel ID</label>
              <input className="input-base" placeholder="Discord channel ID for audit logs"
                value={logChannel} onChange={(e) => setLogChannel(e.target.value)} />
              <p className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
                Ticket and application events will be sent to this channel.
              </p>
            </div>
            <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
              <Save className="w-4 h-4" />
              {saving ? "Saving…" : saved ? "Saved ✓" : "Save Settings"}
            </button>
          </div>

          <div className="glass-card p-6 mt-5">
            <h2 className="font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Bot Invite Link</h2>
            <p className="text-sm mb-3" style={{ color: "var(--text-muted)" }}>
              Share this link to invite RoyalRecruit to another server.
            </p>
            <code className="text-xs px-3 py-2 rounded-lg block" style={{ background: "var(--bg-primary)", color: "var(--crown)", border: "1px solid var(--border)" }}>
              {`https://discord.com/api/oauth2/authorize?client_id=${process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID}&permissions=268438544&scope=bot%20applications.commands`}
            </code>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
}
