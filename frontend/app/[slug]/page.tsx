import { Navbar, Footer } from "../../components/ui";

const PAGES: Record<string, { title: string; body: string[] }> = {
  pricing: { title: "Pricing", body: ["1.5% platform fee by default, configurable per merchant.", "No setup fee. Volume pricing available.", "Fees are snapshotted per transaction so history never changes."] },
  features: { title: "Features", body: ["Payments, invoices, payment links, refunds, wallets, withdrawals.", "API keys, signed webhooks, audit logs, notifications.", "Role-based dashboards for customers, merchants and admins."] },
  security: { title: "Security", body: ["No raw card storage — tokenized/provider-hosted flows only.", "Idempotent payments, HMAC-signed webhooks, RBAC, audit logging.", "Rate limiting, password hashing, email verification."] },
  about: { title: "About PayFlow", body: ["PayFlow is a secure payment platform for businesses of every size.", "Built with Next.js, FastAPI, PostgreSQL and Redis."] },
  contact: { title: "Contact", body: ["Email: support@payflow.example.com", "We respond within 2 business days."] },
  faq: { title: "FAQ", body: ["Is this real money? Local dev uses a DEMO/MOCK provider — clearly labeled.", "Can I add Stripe/SSLCommerz? Yes — implement the provider interface; core logic stays unchanged.", "What about duplicate payments? Idempotency keys prevent them."] },
};

export default function Page({ params }: { params: { slug: string } }) {
  const p = PAGES[params.slug] || { title: params.slug, body: [] };
  return (<><Navbar /><main className="max-w-3xl mx-auto px-4 py-12"><h1 className="text-3xl font-bold">{p.title}</h1>{p.body.map((b, i) => <p key={i} className="text-slate-600 mt-3">{b}</p>)}</main><Footer /></>);
}

export function generateStaticParams() { return Object.keys(PAGES).map((slug) => ({ slug })); }
