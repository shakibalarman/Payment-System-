"use client";
import { useQuery } from "@tanstack/react-query";
import { api, fmtMoney } from "../../lib/api";
import { RequireRole, useAuth } from "../../lib/auth";
import { Shell, ADMIN_NAV, StatCard } from "../../components/ui";

function AdminInner() {
  const { logout } = useAuth();
  const { data } = useQuery({ queryKey: ["admin-ov"], queryFn: () => api("/api/v1/admin/overview") });
  if (!data) return <div className="p-8">Loading…</div>;
  return (
    <Shell nav={ADMIN_NAV}>
      <div className="flex justify-between items-center mb-4"><h1 className="text-2xl font-bold">Admin Dashboard</h1><button className="btn-secondary text-sm" onClick={logout}>Logout</button></div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={String(data.total_users)} />
        <StatCard label="Total Merchants" value={String(data.total_merchants)} />
        <StatCard label="Today's Transactions" value={String(data.today_transactions)} />
        <StatCard label="Today's Volume" value={fmtMoney(data.today_volume)} />
        <StatCard label="Today's Platform Revenue" value={fmtMoney(data.today_fees)} />
        <StatCard label="Pending KYC" value={String(data.pending_kyc)} />
        <StatCard label="Pending Withdrawals" value={String(data.pending_withdrawals)} />
        <StatCard label="Pending Disputes" value={String(data.pending_disputes)} />
      </div>
    </Shell>
  );
}

export default function AdminPage() {
  return <RequireRole roles={["admin"]}><AdminInner /></RequireRole>;
}
