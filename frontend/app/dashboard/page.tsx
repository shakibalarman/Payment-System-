"use client";
import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { api, fmtMoney } from "../../lib/api";
import { RequireRole, useAuth } from "../../lib/auth";
import { Shell, MERCHANT_NAV, StatCard } from "../../components/ui";

function DashboardInner() {
  const { logout } = useAuth();
  const { data, isLoading, error } = useQuery({ queryKey: ["mdash"], queryFn: () => api("/api/v1/merchants/dashboard") });
  if (isLoading) return <div className="p-8">Loading dashboard…</div>;
  if (error) return <div className="p-8">Error: {(error as Error).message}</div>;
  return (
    <Shell nav={MERCHANT_NAV}>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button className="btn-secondary text-sm" onClick={logout}>Logout</button>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Revenue" value={fmtMoney(data.total_revenue)} />
        <StatCard label="Today's Revenue" value={fmtMoney(data.today_revenue)} />
        <StatCard label="Successful Payments" value={String(data.successful_payments)} />
        <StatCard label="Failed Payments" value={String(data.failed_payments)} />
        <StatCard label="Refunds" value={fmtMoney(data.refunds)} />
        <StatCard label="Available Balance" value={fmtMoney(data.available_balance)} />
        <StatCard label="Pending Balance" value={fmtMoney(data.pending_balance)} />
      </div>
      <div className="card p-5 mt-6">
        <h2 className="font-bold mb-3">Revenue (last 14 days)</h2>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data.series.map((s: any) => ({ ...s, revenue: s.revenue / 100 }))}>
            <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={3} />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="revenue" stroke="#1d4ed8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Shell>
  );
}

export default function Dashboard() {
  return <RequireRole roles={["merchant"]}><DashboardInner /></RequireRole>;
}
