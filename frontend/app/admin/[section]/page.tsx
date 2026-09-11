"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, ADMIN_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

const SECTIONS: Record<string, { endpoint: string; cols: string[] }> = {
  users: { endpoint: "/api/v1/admin/users", cols: ["id", "email", "role", "is_suspended"] },
  merchants: { endpoint: "/api/v1/admin/merchants", cols: ["id", "business_name", "email", "kyc_status", "is_suspended"] },
  kyc: { endpoint: "/api/v1/admin/kyc", cols: ["id", "business_name", "owner_name", "kyc_status"] },
  payments: { endpoint: "/api/v1/admin/payments", cols: ["id", "merchant_id", "amount", "status"] },
  refunds: { endpoint: "/api/v1/admin/refunds", cols: ["id", "payment_id", "amount", "status"] },
  withdrawals: { endpoint: "/api/v1/admin/withdrawals", cols: ["id", "merchant_id", "amount", "status"] },
  disputes: { endpoint: "/api/v1/admin/disputes", cols: ["id", "payment_id", "status", "reason"] },
  providers: { endpoint: "/api/v1/admin/providers", cols: ["code", "name", "enabled"] },
  "audit-logs": { endpoint: "/api/v1/admin/audit-logs", cols: ["action", "actor", "resource", "created_at"] },
};

function SectionInner() {
  const { section } = useParams() as { section: string };
  const cfg = SECTIONS[section];
  const [msg, setMsg] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["adm", section], queryFn: () => api(cfg?.endpoint || "/api/v1/admin/overview"), enabled: !!cfg });
  if (!cfg) return <Shell nav={ADMIN_NAV}><p>Unknown section.</p></Shell>;
  const rows: any[] = data?.data || data || [];
  const act = async (url: string, body: any) => {
    const r = await fetch(`${API}${url}`, { method: "POST", headers: H(), body: JSON.stringify(body) }).then((x) => x.json());
    setMsg(r.success ? "Done." : r.error?.message || "Failed");
    refetch();
  };
  return (
    <Shell nav={ADMIN_NAV}>
      <h1 className="text-2xl font-bold mb-4 capitalize">{section}</h1>
      {msg && <p className="text-sm mb-2">{msg}</p>}
      <div className="table-wrap"><table className="data">
        <thead><tr>{cfg.cols.map((c) => <th key={c}>{c}</th>)}<th>Actions</th></tr></thead>
        <tbody>{rows.map((r: any, i: number) => (
          <tr key={i}>{cfg.cols.map((c) => <td key={c} className="break-all">{typeof r[c] === "number" && c === "amount" ? fmtMoney(r[c]) : String(r[c] ?? "—").slice(0, 40)}</td>)}
            <td className="whitespace-nowrap text-xs">
              {section === "kyc" && (<><button className="underline mr-2" onClick={() => act(`/api/v1/admin/kyc/${r.id}`, { approve: true })}>Approve</button><button className="underline" onClick={() => act(`/api/v1/admin/kyc/${r.id}`, { approve: false, reason: "Incomplete documents" })}>Reject</button></>)}
              {section === "withdrawals" && r.status === "PENDING" && (<><button className="underline mr-2" onClick={() => act(`/api/v1/admin/withdrawals/${r.id}`, { approve: true })}>Approve</button><button className="underline" onClick={() => act(`/api/v1/admin/withdrawals/${r.id}`, { approve: false })}>Cancel</button></>)}
              {section === "users" && (<button className="underline" onClick={() => act(`/api/v1/admin/users/${r.id}/suspend`, { suspend: !r.is_suspended })}>{r.is_suspended ? "Unsuspend" : "Suspend"}</button>)}
            </td></tr>
        ))}</tbody>
      </table></div>
    </Shell>
  );
}

export default function AdminSection() {
  return <RequireRole roles={["admin"]}><SectionInner /></RequireRole>;
}
