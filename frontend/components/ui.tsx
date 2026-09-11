import Link from "next/link";
import { ReactNode } from "react";

export function Navbar() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <nav className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between" aria-label="Main">
        <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
        <div className="hidden md:flex gap-6 text-sm">
          {["features", "pricing", "security", "about", "faq", "contact"].map((p) => (
            <Link key={p} href={`/${p}`} className="text-slate-600 hover:text-slate-900 capitalize">{p}</Link>
          ))}
        </div>
        <div className="flex gap-2">
          <Link href="/login" className="btn-secondary text-sm">Sign In</Link>
          <Link href="/register" className="btn-primary text-sm">Get Started</Link>
        </div>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 py-10 grid md:grid-cols-4 gap-8 text-sm text-slate-600">
        <div><p className="font-bold text-slate-900 mb-2">PayFlow</p><p>Secure payment platform for businesses of every size.</p></div>
        <div><p className="font-semibold mb-2">Product</p><p>Payments<br />Invoices<br />Payment Links<br />Withdrawals</p></div>
        <div><p className="font-semibold mb-2">Company</p><p>About<br />Security<br />Pricing<br />Contact</p></div>
        <div><p className="font-semibold mb-2">Developers</p><p>API Docs (/api/docs)<br />Webhooks<br />Status</p></div>
      </div>
    </footer>
  );
}

export function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-5"><p className="text-sm text-slate-500">{label}</p><p className="text-2xl font-bold mt-1">{value}</p></div>
  );
}

export function Sidebar({ items }: { items: { href: string; label: string }[] }) {
  return (
    <aside className="card p-3 md:sticky md:top-16 h-fit" aria-label="Sidebar">
      {items.map((i) => (
        <Link key={i.href} href={i.href} className="block px-3 py-2 rounded-lg text-sm hover:bg-slate-100">{i.label}</Link>
      ))}
    </aside>
  );
}

export const MERCHANT_NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard/payments", label: "Payments" },
  { href: "/dashboard/transactions", label: "Transactions" },
  { href: "/dashboard/payment-links", label: "Payment Links" },
  { href: "/dashboard/invoices", label: "Invoices" },
  { href: "/dashboard/refunds", label: "Refunds" },
  { href: "/dashboard/balance", label: "Balance" },
  { href: "/dashboard/withdrawals", label: "Withdrawals" },
  { href: "/dashboard/customers", label: "Customers" },
  { href: "/dashboard/api-keys", label: "Developer · API Keys" },
  { href: "/dashboard/webhooks", label: "Developer · Webhooks" },
  { href: "/dashboard/notifications", label: "Notifications" },
  { href: "/dashboard/settings", label: "Settings · Profile · KYC" },
];

export const ADMIN_NAV = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/merchants", label: "Merchants" },
  { href: "/admin/kyc", label: "KYC" },
  { href: "/admin/payments", label: "Payments" },
  { href: "/admin/refunds", label: "Refunds" },
  { href: "/admin/withdrawals", label: "Withdrawals" },
  { href: "/admin/disputes", label: "Disputes" },
  { href: "/admin/providers", label: "Providers" },
  { href: "/admin/audit-logs", label: "Audit Logs" },
];

export function Shell({ nav, children }: { nav: { href: string; label: string }[]; children: ReactNode }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-6 grid md:grid-cols-[220px_1fr] gap-6">
      <Sidebar items={nav} />
      <main>{children}</main>
    </div>
  );
}
