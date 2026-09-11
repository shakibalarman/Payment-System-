export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("pf_access");
}

export async function api(path: string, opts: RequestInit = {}) {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(opts.headers as any) };
  const t = getToken();
  if (t) headers["Authorization"] = `Bearer ${t}`;
  const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json?.error?.message || `Request failed (${res.status})`);
  return json.data;
}

export const fmtMoney = (minor: number, currency = "BDT") => {
  const major = (minor / 100).toLocaleString("en-US", { minimumFractionDigits: 2 });
  return `${currency === "BDT" ? "৳" : currency + " "}${major}`;
};

export function statusBadge(status: string) {
  const s = status.toUpperCase();
  if (["SUCCESS", "PAID", "COMPLETED", "APPROVED", "DELIVERED"].includes(s)) return "badge-success";
  if (["PENDING", "PROCESSING", "SENT", "UNDER_REVIEW", "RETRY", "OPEN"].includes(s)) return "badge-warning";
  return "badge-error";
}
