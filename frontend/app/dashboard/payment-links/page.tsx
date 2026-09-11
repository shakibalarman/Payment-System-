"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

function LinksInner() {
  const [form, setForm] = useState({ amount: "1000", description: "Order payment" });
  const [msg, setMsg] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["links"], queryFn: () => api("/api/v1/payment-links") });
  const create = async () => {
    const r = await fetch(`${API}/api/v1/payment-links`, { method: "POST", headers: H(), body: JSON.stringify({ amount: Math.round(parseFloat(form.amount) * 100), description: form.description }) }).then((x) => x.json());
    if (r.success) { setMsg(`Link: ${window.location.origin}${r.data.url}`); refetch(); } else setMsg(r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Payment Links</h1>
      <div className="card p-5">
        <div className="grid sm:grid-cols-2 gap-3">
          <div><label className="label">Amount (major)</label><input className="input" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} /></div>
          <div><label className="label">Description</label><input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        </div>
        <button className="btn-primary mt-3" onClick={create}>Generate link</button>
        {msg && <p className="text-sm mt-2 break-all">{msg}</p>}
      </div>
      <div className="table-wrap mt-6"><table className="data">
        <thead><tr><th>Amount</th><th>Description</th><th>URL</th><th>Active</th></tr></thead>
        <tbody>{(data || []).map((l: any) => <tr key={l.id}><td>{fmtMoney(l.amount, l.currency)}</td><td>{l.description}</td><td className="break-all"><a className="underline" href={l.url}>{l.url}</a></td><td>{String(l.active)}</td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function LinksPage() {
  return <RequireRole roles={["merchant"]}><LinksInner /></RequireRole>;
}
