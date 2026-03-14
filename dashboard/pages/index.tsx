import Head from "next/head";
import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/router";
import { useAuthStore } from "../lib/store";
import { Crown, Shield, Ticket, ClipboardList, ArrowRight, Zap, Lock } from "lucide-react";

export default function Home() {
  const user   = useAuthStore((s) => s.user);
  const router = useRouter();

  useEffect(() => {
    if (user) router.push("/servers");
  }, [user]);

  const DISCORD_CLIENT_ID  = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
  const REDIRECT_URI       = encodeURIComponent(
    process.env.NEXT_PUBLIC_REDIRECT_URI || "http://localhost:3000/api/auth/callback"
  );
  const OAUTH_URL = `https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=identify%20guilds`;

  return (
    <>
      <Head>
        <title>RoyalRecruit – Elite Discord Recruitment</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* ── Hero ── */}
      <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-primary)" }}>
        {/* Nav */}
        <nav className="border-b" style={{ borderColor: "var(--border)" }}>
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Crown className="w-6 h-6" style={{ color: "var(--crown)" }} />
              <span className="font-display text-xl font-semibold gradient-text">RoyalRecruit</span>
            </div>
            <a
              href={OAUTH_URL}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <span>Login with Discord</span>
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </nav>

        {/* Hero section */}
        <main className="flex-1 flex flex-col items-center justify-center px-6 text-center"
              style={{ background: "var(--dark-mesh)" }}>
          {/* Crown icon */}
          <div className="mb-8 relative">
            <div className="w-24 h-24 rounded-full flex items-center justify-center mx-auto"
                 style={{ background: "rgba(201,151,59,0.1)", border: "1px solid rgba(201,151,59,0.3)" }}>
              <Crown className="w-12 h-12" style={{ color: "var(--crown)" }} />
            </div>
            <div className="absolute inset-0 rounded-full animate-pulse-slow"
                 style={{ background: "radial-gradient(circle, rgba(201,151,59,0.15) 0%, transparent 70%)" }} />
          </div>

          <h1 className="font-display text-5xl md:text-7xl font-bold mb-4"
              style={{ color: "var(--text-primary)", lineHeight: 1.1 }}>
            Recruit like<br />
            <span className="gradient-text italic">royalty.</span>
          </h1>

          <p className="text-lg max-w-xl mb-10" style={{ color: "var(--text-muted)" }}>
            The all-in-one Discord bot for elite alliances. Customizable ticket systems,
            structured applications, and a powerful dashboard — all in one place.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
            <a href={OAUTH_URL} className="btn-primary flex items-center gap-2 px-8 py-3 text-base">
              <span>Get Started Free</span>
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href={`https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&permissions=268438544&scope=bot%20applications.commands`}
              target="_blank" rel="noreferrer"
              className="btn-ghost flex items-center gap-2 px-8 py-3 text-base"
            >
              Invite Bot
            </a>
          </div>
        </main>

        {/* Features */}
        <section className="py-20 px-6 border-t" style={{ borderColor: "var(--border)" }}>
          <div className="max-w-5xl mx-auto">
            <h2 className="font-display text-3xl text-center mb-12"
                style={{ color: "var(--text-primary)" }}>
              Everything your server needs
            </h2>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                {
                  icon: <Ticket className="w-6 h-6" />,
                  title: "Smart Tickets",
                  desc: "Customizable ticket types with auto-naming, serial numbers, and staff role assignments.",
                },
                {
                  icon: <ClipboardList className="w-6 h-6" />,
                  title: "Structured Applications",
                  desc: "Build custom Q&A flows that guide applicants through your process step by step.",
                },
                {
                  icon: <Zap className="w-6 h-6" />,
                  title: "Instant Panels",
                  desc: "Send beautiful embed panels with interactive buttons to any channel in seconds.",
                },
                {
                  icon: <Shield className="w-6 h-6" />,
                  title: "Role-based Access",
                  desc: "Staff roles automatically gain access to tickets and applications.",
                },
                {
                  icon: <Lock className="w-6 h-6" />,
                  title: "Secure & Private",
                  desc: "Ticket channels are visible only to the creator and your staff team.",
                },
                {
                  icon: <Crown className="w-6 h-6" />,
                  title: "Multi-Server",
                  desc: "Manage multiple Discord servers from one elegant dashboard.",
                },
              ].map((f) => (
                <div key={f.title} className="glass-card p-6">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                       style={{ background: "rgba(201,151,59,0.12)", color: "var(--crown)" }}>
                    {f.icon}
                  </div>
                  <h3 className="font-semibold mb-2" style={{ color: "var(--text-primary)" }}>{f.title}</h3>
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t py-8 text-center" style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}>
          <div className="flex items-center justify-center gap-2 text-sm">
            <Crown className="w-4 h-4" style={{ color: "var(--crown)" }} />
            <span>RoyalRecruit © {new Date().getFullYear()}</span>
          </div>
        </footer>
      </div>
    </>
  );
}
