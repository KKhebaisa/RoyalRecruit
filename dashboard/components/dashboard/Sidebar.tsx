import Link from "next/link";
import { useRouter } from "next/router";
import { Crown, Ticket, ClipboardList, Layout, Settings, LogOut, ChevronLeft } from "lucide-react";
import { useAuthStore } from "../../lib/store";

const NAV = [
  { label: "Overview",     href: "",             icon: <Crown className="w-4 h-4" /> },
  { label: "Tickets",      href: "/tickets",      icon: <Ticket className="w-4 h-4" /> },
  { label: "Applications", href: "/applications", icon: <ClipboardList className="w-4 h-4" /> },
  { label: "Panels",       href: "/panels",       icon: <Layout className="w-4 h-4" /> },
  { label: "Settings",     href: "/settings",     icon: <Settings className="w-4 h-4" /> },
];

interface SidebarProps {
  guildId: string;
  guildName?: string;
}

export default function Sidebar({ guildId, guildName }: SidebarProps) {
  const router = useRouter();
  const logout = useAuthStore((s) => s.logout);
  const user   = useAuthStore((s) => s.user);

  const base = `/dashboard/${guildId}`;

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <aside
      className="w-64 min-h-screen flex flex-col border-r"
      style={{ background: "var(--bg-surface)", borderColor: "var(--border)" }}
    >
      {/* Logo */}
      <div className="p-6 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2 mb-1">
          <Crown className="w-5 h-5" style={{ color: "var(--crown)" }} />
          <span className="font-display text-lg font-semibold gradient-text">RoyalRecruit</span>
        </div>
        {guildName && (
          <p className="text-xs mt-1 truncate" style={{ color: "var(--text-muted)" }}>
            {guildName}
          </p>
        )}
      </div>

      {/* Back to servers */}
      <div className="px-4 pt-4">
        <Link
          href="/servers"
          className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg transition-colors"
          style={{ color: "var(--text-muted)" }}
        >
          <ChevronLeft className="w-3 h-3" />
          All Servers
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-4 py-2 space-y-1">
        {NAV.map((item) => {
          const href    = `${base}${item.href}`;
          const active  = router.asPath === href || (item.href === "" && router.asPath === base);
          return (
            <Link
              key={item.label}
              href={href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
              style={{
                color:      active ? "var(--crown)" : "var(--text-muted)",
                background: active ? "rgba(201,151,59,0.08)" : "transparent",
                borderLeft: active ? "2px solid var(--crown)" : "2px solid transparent",
              }}
            >
              {item.icon}
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User + logout */}
      <div className="p-4 border-t" style={{ borderColor: "var(--border)" }}>
        {user && (
          <div className="flex items-center gap-3 mb-3">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: "rgba(201,151,59,0.2)", color: "var(--crown)" }}
            >
              {user.username[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                {user.username}
              </p>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors"
          style={{ color: "var(--text-muted)" }}
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
