"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

function WhInner() {
  const [url, setUrl] = useState("https://example.com/webhooks");
  const [msg, setMsg] = useState("");
  const { data: hooks, refetch } = useQuery({ queryKey: ["hooks"], queryFn: () => api("/api/v1/webhooks") });
  const { data: deliveries } = useQuery({ queryKey: ["deliveries"], queryFn: () => api("/api/v1/webhooks/deliveries") });
  const create = async () => {
    const r = await fetch(`${API}/api/v1/webhooks`, { method: "POST", headers: H(), body: JSON.stringify({ url, events: ["payment.success", "payment.failed", "payment.refunded", "withdrawal.completed"] }) }).then((x) => x.json());
    if (r.success) { setMsg(`Webhook secret: ${r.data.secret} — verify HMAC-SHA256(payload, secret)`); refetch(); } else setMsg(r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Developer · Webhooks</h1>
      <div className="card p-5">
        <div className="flex gap-2"><input className="input" value={url} onChange={(e) => setUrl(e.target.value)} aria-label="Webhook URL" /><button className="btn-primary" onClick={create}>Add webhook</button></div>
        {msg && <p className="text-sm mt-2 break-all">{msg}</p>}
        <ul className="text-sm mt-3">{(hooks || []).map((h: any) => <li key={h.id} className="py-1">{h.url} — {h.events.join(", ")}</li>)}</ul>
      </div>
      <h2 className="font-bold mt-6 mb-2">Delivery logs</h2>
      <div className="table-wrap"><table className="data">
        <thead><tr><th>Event</th><th>Status</th><th>Attempts</th><th>Error</th></tr></thead>
        <tbody>{(deliveries || []).map((d: any) => <tr key={d.id}><td>{d.event_type}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(d.status)}`}>{d.status}</span></td><td>{d.attempts}</td><td>{d.last_error || "—"}</td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function WhPage() {
  return <RequireRole roles={["merchant"]}><WhInner /></RequireRole>;
}
