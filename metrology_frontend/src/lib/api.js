/**
 * Central API client for the Legal Metrology Compliance backend.
 *
 * Base URL comes from VITE_API_URL (see .env.example). Every authenticated
 * call automatically attaches the JWT stored by AuthContext.
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TOKEN_KEY = "metrology_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, isForm = false, headers = {} } = {}) {
  const token = getToken();

  const finalHeaders = { ...headers };
  if (!isForm) {
    finalHeaders["Content-Type"] = "application/json";
  }
  if (token) {
    finalHeaders["Authorization"] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
  } catch {
    // The backend is offline/restarting. This is NOT a logout condition:
    // keep the token so the session survives once the server is back.
    throw new ApiError(
      "Cannot reach the server. Check that the backend is running.",
      0,
      null
    );
  }

  if (res.status === 204) {
    return null;
  }

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = typeof data === "object" ? data.detail : data;
    throw new ApiError(
      typeof detail === "string" ? detail : "Request failed",
      res.status,
      detail
    );
  }

  return data;
}

/* ---------------- Auth ---------------- */

export const auth = {
  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: { email, password } }),

  register: (name, email, password, role = "inspector") =>
    request("/api/auth/register", { method: "POST", body: { name, email, password, role } }),

  me: () => request("/api/auth/me"),

  // Exchange the current token for a fresh one (keeps active sessions alive).
  refresh: () => request("/api/auth/refresh", { method: "POST" }),
};

/* ---------------- Scans ---------------- */

export const scans = {
  create: (imageBlob, productName) => {
    const form = new FormData();
    form.append("image", imageBlob, "capture.jpg");
    if (productName) form.append("product_name", productName);
    return request("/api/scans", { method: "POST", body: form, isForm: true });
  },

  // Multi-side scan: send every captured side in one request -> one result.
  createMulti: (imageBlobs, productName) => {
    const form = new FormData();
    imageBlobs.forEach((blob, i) => {
      form.append("images", blob, blob.name || `side_${i + 1}.jpg`);
    });
    if (productName) form.append("product_name", productName);
    return request("/api/scans/multi", { method: "POST", body: form, isForm: true });
  },

  list: (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.set(k, v);
    });
    const qs = query.toString();
    return request(`/api/scans${qs ? `?${qs}` : ""}`);
  },

  get: (id) => request(`/api/scans/${id}`),

  update: (id, payload) => request(`/api/scans/${id}`, { method: "PATCH", body: payload }),

  remove: (id) => request(`/api/scans/${id}`, { method: "DELETE" }),

  reportUrl: (id) => {
    const token = getToken();
    // Reports are streamed as a file response; simplest is to open/download
    // directly with the token appended isn't supported by StaticFiles auth,
    // so we fetch as a blob and trigger a download instead (see downloadReport()).
    return `${API_URL}/api/scans/${id}/report`;
  },

  downloadReport: async (id, filename = "compliance_report.pdf") => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/scans/${id}/report`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Failed to generate report", res.status);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  imageUrl: (imagePath) => {
    if (!imagePath) return null;
    // image_path is stored server-side like "app/uploads/xxx.jpg"
    const filename = imagePath.split("/").pop();
    return `${API_URL}/files/uploads/${filename}`;
  },
};

/* ---------------- Dashboard / Reports ---------------- */

export const dashboard = {
  stats: (period = "Daily") => request(`/api/dashboard/stats?period=${encodeURIComponent(period)}`),
  recentActivity: (limit = 10) => request(`/api/dashboard/recent-activity?limit=${limit}`),

  // All-time analytics PDF generated server-side from real data.
  summaryReport: async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/admin/summary-report`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Failed to generate report", res.status);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `compliance_summary_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

/* ---------------- Admin ---------------- */

export const admin = {
  listUsers: () => request("/api/admin/users"),
  createUser: (payload) => request("/api/admin/users", { method: "POST", body: payload }),
  toggleUser: (id) => request(`/api/admin/users/${id}/toggle-active`, { method: "PATCH" }),
  deleteUser: (id) => request(`/api/admin/users/${id}`, { method: "DELETE" }),
  systemHealth: () => request("/api/admin/system-health"),
  auditLogs: (limit = 50) => request(`/api/admin/audit-logs?limit=${limit}`),
  systemStats: () => request("/api/admin/system-stats"),
  trend: (days = 14) => request(`/api/admin/trend?days=${days}`),
  rules: () => request("/api/admin/rules"),
  backup: () => request("/api/admin/backup", { method: "POST" }),
  summaryReport: async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/admin/summary-report`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Failed to generate report", res.status);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `system_report_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },
};

export { ApiError, API_URL };
