"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { API_URL, fmtMoney } from "../../../lib/api";

export default function ReceiptPage() {
  const { id } = useParams() as { id: string };
  const [r, setR] = useState<any>(null);
  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/receipt/${id}`).then((x) => x.json()).then((j) => setR(j.data));
  }, [id]);
  if (!r) return <main className="p-8">Loading receipt…</main>;
  return (
    <main className="max-w-md mx-auto px-4 py-10">
      <div className="card p-6">
        <h1 className="font-bold text-lg">PayFlow Receipt</h1>
        <dl className="text-sm mt-3 space-y-1">
          {[["Transaction ID", r.transaction_id], ["Payment ID", r.payment_id], ["Merchant", r.merchant?.business_name], ["Customer", r.customer], ["Description", r.description], ["Payment Method", r.payment_method], ["Status", r.status], ["Date", r.date]].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4"><dt className="text-slate-500">{k}</dt><dd className="text-right break-all">{String(v || "—")}</dd></div>
          ))}
          <div className="flex justify-between"><dt className="text-slate-500">Amount</dt><dd>{fmtMoney(r.amount)}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Fee</dt><dd>{fmtMoney(r.fee)}</dd></div>
          <div className="flex justify-between font-bold"><dt>Total</dt><dd>{fmtMoney(r.total)}</dd></div>
        </dl>
        <button className="btn-secondary w-full mt-4" onClick={() => window.print()}>Download / Print Receipt</button>
        <p className="text-center text-sm mt-3"><Link href="/" className="underline">Back to PayFlow</Link></p>
      </div>
    </main>
  );
}
