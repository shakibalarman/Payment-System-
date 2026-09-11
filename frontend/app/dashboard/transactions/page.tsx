"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney, statusBadge } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

function TxnsInner() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const q = `/api/v1/transactions?page=${page}&page_size=20${status ? `&status=${status}` : ""}${search ? `&search=${encodeURIComponent(search)}` : ""}`;
  const { data, isLoading } = useQuery({ queryKey: ["txns", page, status, search], queryFn: () => fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${q}`, { headers: { Authorization: `Bearer ${localStorage.getItem("pf_access")}` } }).then((r) => r.json()) });
  const rows = data?.data || [];
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Transactions</h1>
      <div className="flex flex-wrap gap-2 mb-4">
        <input className="input max-w-xs" placeholder="Search ID, customer…" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search transactions" />
        <select className="input max-w-[200px]" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} aria-label="Filter by status">
          <option value="">All statuses</option>
          {["PENDING", "PROCESSING", "SUCCESS", "FAILED", "CANCELLED"].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      {isLoading ? <p>Loading…</p> : (
        <div className="table-wrap">
          <table className="data">
            <thead><tr><th>Transaction</th><th>Customer</th><th>Amount</th><th>Fee</th><th>Net</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>{rows.map((t: any) => (
              <tr key={t.id}><td><a className="underline" href={`/dashboard/transactions/${t.id}`}>{t.id.slice(0, 8)}…</a></td><td>{t.customer_email}</td><td>{fmtMoney(t.amount, t.currency)}</td><td>{fmtMoney(t.fee_amount, t.currency)}</td><td>{fmtMoney(t.net_amount, t.currency)}</td><td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(t.status)}`}>{t.status}</span></td><td>{t.created_at}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
      <div className="flex gap-2 mt-4">
        <button className="btn-secondary text-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
        <span className="text-sm self-center">Page {data?.pagination?.page} of {Math.max(1, Math.ceil((data?.pagination?.total || 0) / 20))}</span>
        <button className="btn-secondary text-sm" onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </Shell>
  );
}

export default function TxnsPage() {
  return <RequireRole roles={["merchant"]}><TxnsInner /></RequireRole>;
}
