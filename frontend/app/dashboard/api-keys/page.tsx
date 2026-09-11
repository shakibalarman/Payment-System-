"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

function KeysInner() {
  const [name, setName] = useState("Production");
  const [secret, setSecret] = useState("");
  const { data, refetch } = useQuery({ queryKey: ["keys"], queryFn: () => api("/api/v1/api-keys") });
  const create = async () => {
    const r = await fetch(`${API}/api/v1/api-keys`, { method: "POST", headers: H(), body: JSON.stringify({ name }) }).then((x) => x.json());
    if (r.success) { setSecret(r.data.secret); refetch(); }
  };
  const revoke = async (id: string) => {
    await fetch(`${API}/api/v1/api-keys/${id}/revoke`, { method: "POST", headers: H() });
    refetch();
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Developer · API Keys</h1>
      <div className="card p-5">
        <div className="flex gap-2"><input className="input max-w-xs" value={name} onChange={(e) => setName(e.target.value)} aria-label="Key name" /><button className="btn-primary" onClick={create}>Create key</button></div>
        {secret && <p className="text-sm mt-2 break-all bg-amber-50 border border-amber-200 rounded p-2">Secret (shown once): <code>{secret}</code></p>}
      </div>
      <div className="table-wrap mt-6"><table className="data">
        <thead><tr><th>Name</th><th>Prefix</th><th>Revoked</th><th>Last used</th><th></th></tr></thead>
        <tbody>{(data || []).map((k: any) => <tr key={k.id}><td>{k.name}</td><td>{k.prefix}</td><td>{String(k.revoked)}</td><td>{k.last_used_at || "—"}</td><td>{!k.revoked && <button className="underline text-sm" onClick={() => revoke(k.id)}>Revoke</button>}</td></tr>)}</tbody>
      </table></div>
    </Shell>
  );
}

export default function KeysPage() {
  return <RequireRole roles={["merchant"]}><KeysInner /></RequireRole>;
}
