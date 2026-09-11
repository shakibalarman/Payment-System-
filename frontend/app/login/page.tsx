"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "../../lib/auth";

const DEMO_ACCOUNTS = [
  { label: "Customer", email: "customer@payflow.local", password: "Customer123" },
  { label: "Merchant", email: "merchant@payflow.local", password: "Merchant123" },
  { label: "Admin", email: "admin@payflow.local", password: "Admin1234" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [remember, setRemember] = useState(true);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await login(email.trim(), password);
    } catch (ex: any) {
      setErr(ex.message || "Sign in failed. Please check your email and password.");
    } finally {
      setBusy(false);
    }
  };

  const fillDemo = (email: string, password: string) => {
    setEmail(email);
    setPassword(password);
    setErr("");
  };

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-5xl grid md:grid-cols-2 overflow-hidden card">
        {/* Left — brand panel */}
        <section className="hidden md:flex flex-col justify-between bg-slate-900 text-white p-10">
          <div>
            <Link href="/" className="font-bold text-2xl tracking-tight">
              PayFlow<span className="text-brand-500">.</span>
            </Link>
            <h1 className="text-3xl font-extrabold mt-8 leading-tight">
              Accept Payments.
              <br />
              Get Paid Faster.
            </h1>
            <p className="text-slate-300 mt-3 text-sm leading-relaxed">
              Secure checkout, invoices, payment links and wallet ledger — built for businesses of every size.
            </p>
            <ul className="mt-8 space-y-3 text-sm">
              {["Idempotent payments — no double charges", "Signed webhooks + audit logs", "Mock provider for safe DEMO testing"].map((t) => (
                <li key={t} className="flex items-start gap-2.5">
                  <span aria-hidden className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300 text-xs">✓</span>
                  <span className="text-slate-200">{t}</span>
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs text-slate-400 mt-10">
            DEMO environment — no real money moves. Docs at <span className="underline">/api/docs</span>.
          </p>
        </section>

        {/* Right — form */}
        <section className="p-6 sm:p-10">
          <div className="md:hidden mb-6">
            <Link href="/" className="font-bold text-xl text-brand-700">PayFlow.</Link>
          </div>
          <h2 className="text-2xl font-extrabold">Welcome back</h2>
          <p className="text-sm text-slate-500 mt-1">
            Sign in to your account. New here?{" "}
            <Link href="/register" className="text-brand-600 font-medium underline">Create account</Link>
          </p>

          <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
            <div>
              <label className="label" htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="label" htmlFor="pw">Password</label>
                <Link href="/forgot-password" className="text-sm text-brand-600 underline">Forgot password?</Link>
              </div>
              <div className="relative">
                <input
                  id="pw"
                  type={showPw ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="input pr-16"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  aria-label={showPw ? "Hide password" : "Show password"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-sm text-slate-500 hover:text-slate-800 px-2 py-1"
                >
                  {showPw ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4 rounded border-slate-300" />
              Keep me signed in on this device
            </label>

            {err && (
              <p role="alert" className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3.5 py-2.5">{err}</p>
            )}

            <button className="btn-primary w-full disabled:opacity-60" type="submit" disabled={busy || !email || !password}>
              {busy ? "Signing in…" : "Sign In"}
            </button>
          </form>

          <div className="mt-6">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">One-click demo accounts</p>
            <div className="grid grid-cols-3 gap-2 mt-2">
              {DEMO_ACCOUNTS.map((a) => (
                <button
                  key={a.label}
                  type="button"
                  onClick={() => fillDemo(a.email, a.password)}
                  className="btn-secondary text-sm px-2 py-2"
                  title={`${a.email} / ${a.password}`}
                >
                  {a.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-2">Click to fill, then hit Sign In. Passwords are dev-only.</p>
          </div>

          <p className="text-xs text-slate-400 mt-6 text-center">
            Protected by rate limits, RBAC and audit logs. Never share your password.
          </p>
        </section>
      </div>
    </main>
  );
}
