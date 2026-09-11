"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, fmtMoney, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

function PaymentsInner() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ amount: "5000", currency: "BDT", description: "Website Development", customer_email: "customer@example.com" });
  const [msg, setMsg] = useState("");
  const { data } = useQuery({ queryKey: ["payments"], queryFn: () => api("/api/v1/payments?page=1&page_size=20") });
  const create = useMutation({
    mutationFn: () =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/payments`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}`, "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ ...form, amount: Math.round(parseFloat(form.amount) * 100) }),
      }).then((r) => r.json()),
    onSuccess: (j) => {
      if (j.success) { setMsg(`Created. Checkout: ${j.data.checkout_url}`); qc.invalidateQueries({ queryKey: ["payments"] }); }
      else setMsg(j.error?.message || "Failed");
    },
  });
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Payments</h1>
      <div className="card p-5">
        <h2 className="font-bold">Create payment request</h2>
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <div><label className="label">Amount (major units)</label><input className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></div>
          <div><label className="label">Currency</label><input className="input" value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></div>
          <div><label className="label">Description</label><input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
          <div><label className="label">Customer email</label><input className="input" value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" onClick={() => create.mutate()}>Create payment</button>
        {msg && <p className="text-sm mt-2">{msg}</p>}
      </div>
      <div className="table-wrap mt-6">
        <table className="data">
          <thead><tr><th>ID</th><th>Customer</th><th>Amount</th><th>Status</th><th>Created</th></tr></thead>
          <tbody>{(Array.isArray(data) ? data : []).map((p: any) => (
            <tr key={p.id}><td><a className="underline" href={`/dashboard/transactions?search=${p.id}`}>{p.id.slice(0, 8)}…</a></td><td>{p.customer_email}</td><td>{fmtMoney(p.amount, p.currency)}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(p.status)}`}>{p.status}</span></td><td>{p.created_at}</td></tr>
          ))}</tbody>
        </table>
      </div>
    </Shell>
  );
}

export default function PaymentsPage() {
  return <RequireRole roles={["merchant"]}><PaymentsInner /></RequireRole>;
}
