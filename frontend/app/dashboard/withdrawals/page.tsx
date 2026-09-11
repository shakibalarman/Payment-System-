"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function WdInner() {
  const [form, setForm] = useState({ amount: "", destination: "" });
  const [msg, setMsg] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["wds"], queryFn: () => api("/api/v1/withdrawals") });
  const create = async () => {
    const r = await fetch(`${API}/api/v1/withdrawals`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` }, body: JSON.stringify({ amount: Math.round(parseFloat(form.amount || "0") * 100), destination: form.destination }) }).then((x) => x.json());
    if (r.success) { setMsg(`Withdrawal ${r.data.status}`); refetch(); } else setMsg(r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Withdrawals</h1>
      <div className="card p-5">
        <div className="grid sm:grid-cols-2 gap-3">
          <div><label className="label">Amount (major)</label><input className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></div>
          <div><label className="label">Destination (bank account)</label><input className="input" value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" onClick={create}>Request withdrawal</button>
        {msg && <p className="text-sm mt-2">{msg}</p>}
      </div>
      <div className="table-wrap mt-6"><table className="data">
        <thead><tr><th>Amount</th><th>Destination</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>{(data || []).map((w: any) => <tr key={w.id}><td>{fmtMoney(w.amount)}</td><td>{w.destination}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(w.status)}`}>{w.status}</span></td><td>{w.created_at}</td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function WdPage() {
  return <RequireRole roles={["merchant"]}><WdInner /></RequireRole>;
}
