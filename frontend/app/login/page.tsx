"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "../../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const submit = async (e: any) => {
    e.preventDefault();
    setErr("");
    try { await login(email, password); } catch (ex: any) { setErr(ex.message); }
  };
  return (
    <main className="max-w-md mx-auto px-4 py-16">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <h1 className="text-2xl font-bold mt-4">Sign In</h1>
      <form onSubmit={submit} className="card p-6 mt-4 space-y-4">
        <div><label className="label" htmlFor="email">Email</label><input id="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        <div><label className="label" htmlFor="pw">Password</label><input id="pw" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required /></div>
        {err && <p role="alert" className="text-sm text-rose-600">{err}</p>}
        <button className="btn-primary w-full" type="submit">Sign In</button>
        <p className="text-sm text-slate-600"><Link href="/forgot-password" className="underline">Forgot password?</Link> · <Link href="/register" className="underline">Create account</Link></p>
      </form>
    </main>
  );
}
