"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function RefundsInner() {
  const [form, setForm] = useState({ payment_id: "", amount: "" });
  const [msg, setMsg] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["refunds"], queryFn: () => api("/api/v1/refunds") });
  const create = async () => {
    const r = await fetch(`${API}/api/v1/refunds`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}`, "Idempotency-Key": crypto.randomUUID() }, body: JSON.stringify({ payment_id: form.payment_id, amount: form.amount ? Math.round(parseFloat(form.amount) * 100) : null, reason: "merchant request" }) }).then((x) => x.json());
    if (r.success) { setMsg(`Refund ${r.data.id} ${r.data.status}`); refetch(); } else setMsg(r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Refunds</h1>
      <div className="card p-5">
        <div className="grid sm:grid-cols-2 gap-3">
          <div><label className="label">Payment ID</label><input className="input" value={form.payment_id} onChange={(e) => setForm({ ...form, payment_id: e.target.value })} /></div>
          <div><label className="label">Amount (major, blank = full)</label><input className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" onClick={create}>Issue refund</button>
        {msg && <p className="text-sm mt-2">{msg}</p>}
      </div>
      <div className="table-wrap mt-6"><table className="data">
        <thead><tr><th>ID</th><th>Payment</th><th>Amount</th><th>Status</th></tr></thead>
        <tbody>{((data as any)?.data || data || []).map((r: any) => <tr key={r.id}><td>{r.id.slice(0, 8)}…</td><td>{r.payment_id.slice(0, 8)}…</td><td>{fmtMoney(r.amount)}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(r.status)}`}>{r.status}</span></td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function RefundsPage() {
  return <RequireRole roles={["merchant"]}><RefundsInner /></RequireRole>;
}
