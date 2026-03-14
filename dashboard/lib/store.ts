/**
 * Global auth state managed with Zustand.
 */

import { create } from "zustand";

interface User {
  discord_id: string;
  username: string;
  avatar: string | null;
}

interface AuthState {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user:  null,
  token: null,

  setAuth: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("rr_token", token);
      localStorage.setItem("rr_user",  JSON.stringify(user));
    }
    set({ user, token });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("rr_token");
      localStorage.removeItem("rr_user");
    }
    set({ user: null, token: null });
  },

  hydrate: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("rr_token");
    const raw   = localStorage.getItem("rr_user");
    if (token && raw) {
      try {
        const user = JSON.parse(raw) as User;
        set({ user, token });
      } catch {
        /* ignore */
      }
    }
  },
}));
