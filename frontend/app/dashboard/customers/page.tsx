"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

export default function CustomersPage() {
  return (
    <RequireRole roles={["merchant"]}>
      <Shell nav={MERCHANT_NAV}>
        <h1 className="text-2xl font-bold mb-4">Customers</h1>
        <CustomerTable />
      </Shell>
    </RequireRole>
  );
}

function CustomerTable() {
  const { data } = useQuery({ queryKey: ["customers"], queryFn: () => api("/api/v1/customers") });
  return (
    <div className="table-wrap"><table className="data">
      <thead><tr><th>Name</th><th>Email</th><th>Since</th></tr></thead>
      <tbody>{(data || []).map((c: any) => <tr key={c.id}><td>{c.name || "—"}</td><td>{c.email}</td><td>{c.created_at}</td></tr>)}</tbody>
    </table></div>
  );
}
