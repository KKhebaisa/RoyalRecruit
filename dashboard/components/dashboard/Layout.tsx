import { useRouter } from "next/router";
import { useEffect, ReactNode } from "react";
import { useAuthStore } from "../../lib/store";
import Sidebar from "./Sidebar";

interface DashboardLayoutProps {
  children: ReactNode;
  guildId:  string;
  guildName?: string;
}

export default function DashboardLayout({ children, guildId, guildName }: DashboardLayoutProps) {
  const user   = useAuthStore((s) => s.user);
  const router = useRouter();

  useEffect(() => {
    if (!user) router.push("/");
  }, [user]);

  if (!user) return null;

  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-primary)" }}>
      <Sidebar guildId={guildId} guildName={guildName} />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
