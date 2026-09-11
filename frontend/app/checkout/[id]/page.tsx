"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL, fmtMoney } from "../../../lib/api";

export default function CheckoutPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const [info, setInfo] = useState<any>(null);
  const [method, setMethod] = useState("card");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => fetch(`${API_URL}/api/v1/public/checkout/${id}`).then((r) => r.json()).then((j) => setInfo(j.data));
  useEffect(() => { load(); }, [id]);

  const pay = async (outcome: string) => {
    setBusy(true); setErr("");
    try {
      // Idempotency-Key prevents duplicate charges on double-click (Case 1)
      const r = await fetch(`${API_URL}/api/v1/public/checkout/${id}/pay`, {
        method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": `checkout-${id}` },
        body: JSON.stringify({ payment_method: method, outcome }),
      }).then((x) => x.json());
      if (!r.success) throw new Error(r.error?.message);
      router.push(`/receipt/${id}`);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  if (!info) return <main className="p-8">Loading checkout…</main>;
  return (
    <main className="max-w-md mx-auto px-4 py-10">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <div className="card p-6 mt-4">
        <h1 className="font-bold text-lg">Order</h1>
        {info.demo && <p className="text-xs font-bold text-amber-700 bg-amber-100 rounded px-2 py-1 mt-2 inline-block">DEMO / MOCK PAYMENT — no real money</p>}
        <dl className="text-sm mt-3 space-y-1">
          <div className="flex justify-between"><dt>Description</dt><dd>{info.description || "—"}</dd></div>
          <div className="flex justify-between"><dt>Amount</dt><dd>{fmtMoney(info.amount, info.currency)}</dd></div>
          <div className="flex justify-between"><dt>Fees</dt><dd>{fmtMoney(info.fee_amount || 0, info.currency)}</dd></div>
          <div className="flex justify-between font-bold"><dt>Total</dt><dd>{fmtMoney(info.amount, info.currency)}</dd></div>
          <div className="flex justify-between"><dt>Status</dt><dd>{info.status}</dd></div>
        </dl>
        <fieldset className="mt-4">
          <legend className="label">Payment Method</legend>
          {(["card", "mobile_banking", "bank_transfer"] as const).map((m) => (
            <label key={m} className="flex items-center gap-2 text-sm py-1">
              <input type="radio" name="pm" checked={method === m} onChange={() => setMethod(m)} /> {m.replace("_", " ")}
            </label>
          ))}
        </fieldset>
        {err && <p role="alert" className="text-sm text-rose-600 mt-2">{err}</p>}
        <button className="btn-primary w-full mt-4" disabled={busy || !["PENDING", "PROCESSING"].includes(info.status)} onClick={() => pay("SUCCESS")}>
          {busy ? "Processing…" : "Pay Now"}
        </button>
        <button className="text-xs text-slate-500 underline mt-2" onClick={() => pay("FAILED")}>Simulate failed payment (demo)</button>
        <p className="text-xs text-slate-500 mt-3">Secure Payment · status is confirmed by the backend, never the frontend.</p>
      </div>
    </main>
  );
}
