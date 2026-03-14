/**
 * Axios instance pre-configured for the RoyalRecruit backend.
 * JWT is read from localStorage and injected on every request.
 */

import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT from localStorage
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("rr_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("rr_token");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

// ── Helper methods ────────────────────────────────────────────────────────────

export const authAPI = {
  callback: (code: string) =>
    api.post("/api/auth/callback", null, { params: { code } }),
  me: () => api.get("/api/auth/me"),
  guilds: () => api.get("/api/auth/guilds"),
};

export const guildsAPI = {
  get: (guildId: string) => api.get(`/api/guilds/${guildId}`),
  updateSettings: (guildId: string, data: any) =>
    api.patch(`/api/guilds/${guildId}/settings`, data),
};

export const ticketsAPI = {
  listTypes: (guildId: string) => api.get(`/api/tickets/${guildId}/types`),
  createType: (guildId: string, data: any) =>
    api.post(`/api/tickets/${guildId}/types`, data),
  updateType: (guildId: string, typeId: number, data: any) =>
    api.put(`/api/tickets/${guildId}/types/${typeId}`, data),
  deleteType: (guildId: string, typeId: number) =>
    api.delete(`/api/tickets/${guildId}/types/${typeId}`),
  listTickets: (guildId: string) => api.get(`/api/tickets/${guildId}/list`),
};

export const applicationsAPI = {
  listTypes: (guildId: string) => api.get(`/api/applications/${guildId}/types`),
  createType: (guildId: string, data: any) =>
    api.post(`/api/applications/${guildId}/types`, data),
  updateType: (guildId: string, typeId: number, data: any) =>
    api.put(`/api/applications/${guildId}/types/${typeId}`, data),
  deleteType: (guildId: string, typeId: number) =>
    api.delete(`/api/applications/${guildId}/types/${typeId}`),
  listApplications: (guildId: string) =>
    api.get(`/api/applications/${guildId}/list`),
};

export const panelsAPI = {
  list: (guildId: string) => api.get(`/api/panels/${guildId}`),
  create: (guildId: string, data: any) => api.post(`/api/panels/${guildId}`, data),
  delete: (guildId: string, panelId: number) =>
    api.delete(`/api/panels/${guildId}/${panelId}`),
};

export const logsAPI = {
  list: (guildId: string) => api.get(`/api/logs/${guildId}`),
};
