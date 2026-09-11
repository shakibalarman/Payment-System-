"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL, fmtMoney } from "../../../lib/api";

export default function PayLinkPage() {
  const { token } = useParams() as { token: string };
  const router = useRouter();
  const [info, setInfo] = useState<any>(null);
  const [email, setEmail] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/pay/${token}`).then((r) => r.json()).then((j) => { if (j.success) setInfo(j.data); else setErr(j.error?.message || "Invalid link"); });
  }, [token]);

  const go = async (e: any) => {
    e.preventDefault();
    const r = await fetch(`${API_URL}/api/v1/public/pay/${token}`, { method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": `link-${token}-${email}` }, body: JSON.stringify({ customer_email: email }) }).then((x) => x.json());
    if (r.success) router.push(`/checkout/${r.data.id}`);
    else setErr(r.error?.message || "Failed");
  };

  return (
    <main className="max-w-md mx-auto px-4 py-10">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <div className="card p-6 mt-4">
        <h1 className="font-bold">Payment Link</h1>
        {err && <p role="alert" className="text-sm text-rose-600 mt-2">{err}</p>}
        {info && (<><p className="text-sm text-slate-600 mt-2">{info.description}</p><p className="text-2xl font-bold mt-2">{fmtMoney(info.amount, info.currency)}</p>
          <form onSubmit={go} className="mt-4 space-y-3">
            <div><label className="label" htmlFor="em">Your email</label><input id="em" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
            <button className="btn-primary w-full">Continue to checkout</button>
          </form></>)}
      </div>
    </main>
  );
}
