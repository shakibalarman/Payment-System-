"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, fmtMoney, statusBadge } from "../../../../lib/api";
import { RequireRole } from "../../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../../components/ui";

function Detail() {
  const { id } = useParams() as { id: string };
  const [t, setT] = useState<any>(null);
  useEffect(() => { api(`/api/v1/transactions/${id}`).then(setT); }, [id]);
  if (!t) return <div className="p-8">Loading…</div>;
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Transaction details</h1>
      <div className="card p-5 text-sm space-y-1">
        {[["Transaction ID", t.id], ["Payment ID", t.payment_id], ["Customer", t.customer_email], ["Amount", fmtMoney(t.amount, t.currency)], ["Fee", fmtMoney(t.fee_amount, t.currency)], ["Net", fmtMoney(t.net_amount, t.currency)], ["Method", t.payment_method], ["Provider", t.provider], ["Created", t.created_at]].map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4"><span className="text-slate-500">{k}</span><span className="break-all text-right">{String(v || "—")}</span></div>
        ))}
        <p><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(t.status)}`}>{t.status}</span></p>
      </div>
    </Shell>
  );
}

export default function TxnDetailPage() {
  return <RequireRole roles={["merchant"]}><Detail /></RequireRole>;
}
