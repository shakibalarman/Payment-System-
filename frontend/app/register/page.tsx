"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "../../lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const [v, setV] = useState({ email: "", password: "", full_name: "", role: "merchant" });
  const [err, setErr] = useState("");
  const submit = async (e: any) => {
    e.preventDefault();
    setErr("");
    try { await register(v); } catch (ex: any) { setErr(ex.message); }
  };
  const set = (k: string) => (e: any) => setV({ ...v, [k]: e.target.value });
  return (
    <main className="max-w-md mx-auto px-4 py-16">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <h1 className="text-2xl font-bold mt-4">Get Started</h1>
      <form onSubmit={submit} className="card p-6 mt-4 space-y-4">
        <div><label className="label" htmlFor="name">Full name</label><input id="name" className="input" value={v.full_name} onChange={set("full_name")} required /></div>
        <div><label className="label" htmlFor="email">Email</label><input id="email" className="input" value={v.email} onChange={set("email")} required /></div>
        <div><label className="label" htmlFor="pw">Password (8+ chars, uppercase + digit)</label><input id="pw" type="password" className="input" value={v.password} onChange={set("password")} required /></div>
        <div><label className="label" htmlFor="role">Account type</label>
          <select id="role" className="input" value={v.role} onChange={set("role")}><option value="merchant">Merchant</option><option value="customer">Customer</option></select></div>
        {err && <p role="alert" className="text-sm text-rose-600">{err}</p>}
        <button className="btn-primary w-full" type="submit">Create account</button>
        <p className="text-sm text-slate-600"><Link href="/login" className="underline">Already have an account?</Link></p>
      </form>
    </main>
  );
}
