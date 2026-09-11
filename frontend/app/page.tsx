import Link from "next/link";
import { Navbar, Footer } from "../components/ui";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <section className="max-w-7xl mx-auto px-4 py-16 text-center">
          <p className="text-sm font-semibold text-brand-600">TRUSTED PAYMENT INFRASTRUCTURE</p>
          <h1 className="text-4xl md:text-6xl font-extrabold mt-3">Accept Payments.<br />Get Paid Faster.</h1>
          <p className="text-lg text-slate-600 mt-4">A secure payment platform for businesses of every size.</p>
          <div className="mt-6 flex gap-3 justify-center">
            <Link href="/register" className="btn-primary">Get Started</Link>
            <Link href="/login" className="btn-secondary">Sign In</Link>
          </div>
        </section>
        <section className="max-w-7xl mx-auto px-4 grid md:grid-cols-3 gap-4">
          {[["Invoices", "Create and send professional invoices with a Pay button."], ["Payment Links", "Share a link, get paid. No website required."], ["Developer APIs", "API keys, webhooks with HMAC signatures, audit logs."]].map(([t, d]) => (
            <div key={t} className="card p-6"><h2 className="font-bold text-lg">{t}</h2><p className="text-slate-600 mt-2 text-sm">{d}</p></div>
          ))}
        </section>
        <section className="max-w-7xl mx-auto px-4 py-12">
          <h2 className="text-2xl font-bold">How it works</h2>
          <ol className="mt-4 grid md:grid-cols-4 gap-4 text-sm">
            {["Merchant creates a payment, invoice or link", "Customer opens secure checkout", "Backend verifies the result (never the frontend)", "Balance, receipt, webhook & notification update"].map((s, i) => (
              <li key={i} className="card p-4"><span className="font-bold">{i + 1}.</span> {s}</li>
            ))}
          </ol>
        </section>
        <section className="max-w-7xl mx-auto px-4 grid md:grid-cols-3 gap-4 text-sm">
          <div className="card p-6"><h3 className="font-bold">Payment methods</h3><p className="text-slate-600 mt-2">Card · Mobile Banking · Bank Transfer (via provider abstraction; demo uses a Mock provider — no real money).</p></div>
          <div className="card p-6"><h3 className="font-bold">Security</h3><p className="text-slate-600 mt-2">No raw card storage, idempotent payments, signed webhooks, RBAC, audit logs.</p></div>
          <div className="card p-6"><h3 className="font-bold">Pricing</h3><p className="text-slate-600 mt-2">1.5% platform fee by default, configurable per merchant. <Link href="/pricing" className="text-brand-600 underline">See pricing</Link></p></div>
        </section>
        <section className="max-w-7xl mx-auto px-4 py-12">
          <h2 className="text-2xl font-bold">FAQ</h2>
          <div className="mt-4 grid md:grid-cols-2 gap-4 text-sm">
            <div className="card p-4"><p className="font-semibold">Is this real money?</p><p className="text-slate-600">Local development uses a clearly-labeled DEMO/MOCK provider. Connect a real provider (Stripe/SSLCommerz/…) via the provider abstraction for production.</p></div>
            <div className="card p-4"><p className="font-semibold">Do you store card numbers?</p><p className="text-slate-600">Never. Only tokenized references.</p></div>
          </div>
        </section>
        <section className="max-w-7xl mx-auto px-4 pb-16 text-center">
          <Link href="/register" className="btn-primary">Start accepting payments</Link>
        </section>
      </main>
      <Footer />
    </>
  );
}
