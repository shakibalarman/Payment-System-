"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL, fmtMoney } from "../../../lib/api";

export default function InvoicePayPage() {
  const { token } = useParams() as { token: string };
  const router = useRouter();
  const [inv, setInv] = useState<any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/invoice/${token}`).then((r) => r.json()).then((j) => { if (j.success) setInv(j.data); else setErr("Invoice not found"); });
  }, [token]);
  const pay = async () => {
    const r = await fetch(`${API_URL}/api/v1/public/invoice/${token}/pay`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": `inv-${token}` }, body: JSON.stringify({}) }).then((x) => x.json());
    if (r.success) router.push(`/checkout/${r.data.id}`);
    else setErr(r.error?.message || "Failed");
  };
  return (
    <main className="max-w-md mx-auto px-4 py-10">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <div className="card p-6 mt-4">
        <h1 className="font-bold">Invoice {inv?.invoice_no}</h1>
        {err && <p role="alert" className="text-sm text-rose-600">{err}</p>}
        {inv && (<><ul className="text-sm mt-3">{inv.items.map((i: any, k: number) => <li key={k} className="flex justify-between"><span>{i.name} × {i.quantity}</span><span>{fmtMoney(i.unit_price * i.quantity, inv.currency)}</span></li>)}</ul>
          <p className="font-bold mt-3">Total: {fmtMoney(inv.total, inv.currency)}</p>
          <p className="text-sm">Status: {inv.status}</p>
          {inv.status !== "PAID" && <button className="btn-primary w-full mt-4" onClick={pay}>Pay Invoice</button>}</>)}
      </div>
    </main>
  );
}
