"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api, fmtMoney, statusBadge } from "../../lib/api";
import { RequireRole, useAuth } from "../../lib/auth";

function CustomerInner() {
  const { logout, user } = useAuth();
  const { data: payments } = useQuery({ queryKey: ["cpay"], queryFn: () => api("/api/v1/customer/payments") });
  const { data: methods } = useQuery({ queryKey: ["pm"], queryFn: () => api("/api/v1/payment-methods") });
  return (
    <main className="max-w-5xl mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">My Payments ({user?.email})</h1>
        <button className="btn-secondary text-sm" onClick={logout}>Logout</button>
      </div>
      <div className="table-wrap"><table className="data">
        <thead><tr><th>Description</th><th>Amount</th><th>Status</th><th>Receipt</th></tr></thead>
        <tbody>{(payments || []).map((p: any) => <tr key={p.id}><td>{p.description}</td><td>{fmtMoney(p.amount, p.currency)}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(p.status)}`}>{p.status}</span></td><td><Link className="underline" href={`/receipt/${p.id}`}>Receipt</Link></td></tr>)}</tbody>
      </table></div>
      <h2 className="font-bold mt-6 mb-2">Saved payment methods (tokenized only)</h2>
      <ul className="text-sm">{(methods || []).map((m: any) => <li key={m.id} className="card p-3 mb-2">{m.method_type} · {m.brand} ·••• {m.last4}</li>)}{(methods || []).length === 0 && <p className="text-sm text-slate-500">No saved methods.</p>}</ul>
    </main>
  );
}

export default function CustomerPage() {
  return <RequireRole roles={["customer"]}><CustomerInner /></RequireRole>;
}
