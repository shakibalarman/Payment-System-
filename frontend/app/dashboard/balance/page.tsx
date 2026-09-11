"use client";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

function BalanceInner() {
  const { data, isLoading } = useQuery({ queryKey: ["wallet"], queryFn: () => api("/api/v1/wallet") });
  if (isLoading) return <div className="p-8">Loading…</div>;
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Balance</h1>
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="card p-5"><p className="text-sm text-slate-500">Available</p><p className="text-2xl font-bold">{fmtMoney(data.available)}</p></div>
        <div className="card p-5"><p className="text-sm text-slate-500">Pending</p><p className="text-2xl font-bold">{fmtMoney(data.pending)}</p></div>
        <div className="card p-5"><p className="text-sm text-slate-500">Total</p><p className="text-2xl font-bold">{fmtMoney(data.total)}</p></div>
      </div>
      <h2 className="font-bold mt-6 mb-2">Ledger (auditable — every movement recorded)</h2>
      <div className="table-wrap"><table className="data">
        <thead><tr><th>Kind</th><th>Amount</th><th>Balance after</th><th>Reference</th><th>Date</th></tr></thead>
        <tbody>{data.ledger.map((t: any) => <tr key={t.id}><td>{t.kind}</td><td>{fmtMoney(t.amount)}</td><td>{fmtMoney(t.balance_after)}</td><td>{t.reference_type}</td><td>{t.created_at}</td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function BalancePage() {
  return <RequireRole roles={["merchant"]}><BalanceInner /></RequireRole>;
}
