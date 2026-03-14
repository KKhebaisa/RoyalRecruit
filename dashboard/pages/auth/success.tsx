/**
 * /auth/success
 * Reads token from query params, stores in localStorage, redirects to /servers.
 */

import { useEffect } from "react";
import { useRouter } from "next/router";
import { useAuthStore } from "../../lib/store";
import { Crown } from "lucide-react";

export default function AuthSuccess() {
  const router  = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  useEffect(() => {
    const { token, username, avatar, id } = router.query as Record<string, string>;
    if (token && username && id) {
      setAuth({ discord_id: id, username, avatar: avatar || null }, token);
      router.replace("/servers");
    }
  }, [router.query]);

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--bg-primary)" }}>
      <div className="text-center">
        <Crown className="w-12 h-12 mx-auto mb-4 animate-pulse" style={{ color: "var(--crown)" }} />
        <p style={{ color: "var(--text-muted)" }}>Logging you in…</p>
      </div>
    </div>
  );
}
