"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, fmtMoney } from "../../../../lib/api";
import { RequireRole } from "../../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../../components/ui";

function Detail() {
  const { id } = useParams() as { id: string };
  const [inv, setInv] = useState<any>(null);
  useEffect(() => { api(`/api/v1/invoices/${id}`).then(setInv); }, [id]);
  if (!inv) return <div className="p-8">Loading…</div>;
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Invoice {inv.invoice_no}</h1>
      <div className="card p-5 text-sm">
        <p>Customer: {inv.customer_name} ({inv.customer_email})</p>
        <ul className="mt-2">{inv.items.map((i: any, k: number) => <li key={k} className="flex justify-between"><span>{i.name} × {i.quantity}</span><span>{fmtMoney(i.unit_price * i.quantity)}</span></li>)}</ul>
        <p className="font-bold mt-2">Total: {fmtMoney(inv.total)} · Status: {inv.status}</p>
        <p className="mt-2 break-all">Public pay URL: <a className="underline" href={`/invoice/${inv.public_token}`}>/invoice/{inv.public_token}</a></p>
      </div>
    </Shell>
  );
}

export default function InvoiceDetail() {
  return <RequireRole roles={["merchant"]}><Detail /></RequireRole>;
}
