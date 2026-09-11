"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function NotifInner() {
  const { data, refetch } = useQuery({ queryKey: ["notif"], queryFn: () => api("/api/v1/notifications") });
  const mark = async (id: string) => {
    await fetch(`${API}/api/v1/notifications/${id}/read`, { method: "POST", headers: { Authorization: `Bearer ${localStorage.getItem("pf_access")}` } });
    refetch();
  };
  const items = (data as any)?.data || data || [];
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Notifications</h1>
      <div className="space-y-2">{items.map((n: any) => (
        <div key={n.id} className={`card p-4 ${n.read ? "opacity-70" : ""}`}>
          <p className="font-semibold text-sm">{n.title} <span className="text-slate-400">· {n.type}</span></p>
          <p className="text-sm text-slate-600">{n.body}</p>
          {!n.read && <button className="text-xs underline mt-1" onClick={() => mark(n.id)}>Mark read</button>}
        </div>
      ))}{items.length === 0 && <p className="text-sm text-slate-500">No notifications yet.</p>}</div>
    </Shell>
  );
}

export default function NotifPage() {
  return <RequireRole roles={["merchant", "customer", "admin"]}><NotifInner /></RequireRole>;
}
