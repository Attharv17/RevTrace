import axios from "axios";

/**
 * Axios instance pre-configured for the LedgerPilot API.
 * In dev, Vite proxies /api → http://localhost:8000
 * In prod, set VITE_API_BASE_URL in .env
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ── Request interceptor (auth headers will go here in Phase 3) ──────────────
apiClient.interceptors.request.use((config) => {
  // const token = localStorage.getItem("lp_access_token");
  // if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor ─────────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ?? error.message ?? "Unknown error";
    console.error("[LedgerPilot API Error]", message, error.response?.status);
    return Promise.reject(error);
  }
);

export default apiClient;

// ── Typed helper functions ───────────────────────────────────────────────────
export const api = {
  get:    <T>(url: string)             => apiClient.get<T>(url).then((r) => r.data),
  post:   <T>(url: string, data: unknown) => apiClient.post<T>(url, data).then((r) => r.data),
  put:    <T>(url: string, data: unknown) => apiClient.put<T>(url, data).then((r) => r.data),
  delete: <T>(url: string)             => apiClient.delete<T>(url).then((r) => r.data),
};
