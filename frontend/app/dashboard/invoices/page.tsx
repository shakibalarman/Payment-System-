"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

function InvoicesInner() {
  const [form, setForm] = useState({ customer_name: "", customer_email: "", item: "Service", qty: "1", price: "5000" });
  const [msg, setMsg] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["invs"], queryFn: () => api("/api/v1/invoices") });
  const rows = data?.data || [];
  const create = async () => {
    const r = await fetch(`${API}/api/v1/invoices`, { method: "POST", headers: H(), body: JSON.stringify({
      customer_name: form.customer_name, customer_email: form.customer_email,
      items: [{ name: form.item, quantity: parseInt(form.qty), unit_price: Math.round(parseFloat(form.price) * 100) }],
    }) }).then((x) => x.json());
    if (r.success) { setMsg(`Invoice ${r.data.invoice_no} created. Pay URL: /invoice/${r.data.public_token}`); refetch(); } else setMsg(r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Invoices</h1>
      <div className="card p-5">
        <h2 className="font-bold">Create invoice</h2>
        <div className="grid sm:grid-cols-2 gap-3 mt-3">
          <div><label className="label">Customer name</label><input className="input" value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} /></div>
          <div><label className="label">Customer email</label><input className="input" value={form.customer_email} onChange={(e) => setForm({ ...form, customer_email: e.target.value })} /></div>
          <div><label className="label">Item</label><input className="input" value={form.item} onChange={(e) => setForm({ ...form, item: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-2">
            <div><label className="label">Qty</label><input className="input" value={form.qty} onChange={(e) => setForm({ ...form, qty: e.target.value })} /></div>
            <div><label className="label">Unit price</label><input className="input" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} /></div>
          </div>
        </div>
        <button className="btn-primary mt-3" onClick={create}>Create invoice</button>
        {msg && <p className="text-sm mt-2 break-all">{msg}</p>}
      </div>
      <div className="table-wrap mt-6"><table className="data">
        <thead><tr><th>Invoice</th><th>Customer</th><th>Total</th><th>Status</th></tr></thead>
        <tbody>{rows.map((i: any) => <tr key={i.id}><td><a className="underline" href={`/dashboard/invoices/${i.id}`}>{i.invoice_no}</a></td><td>{i.customer_email}</td><td>{fmtMoney(i.total)}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(i.status)}`}>{i.status}</span></td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function InvoicesPage() {
  return <RequireRole roles={["merchant"]}><InvoicesInner /></RequireRole>;
}
