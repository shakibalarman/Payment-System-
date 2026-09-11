"use client";
import { useState } from "react";
import Link from "next/link";
import { API_URL } from "../lib/api";

export default function TokenPage({ mode }: { mode: "forgot" | "reset" }) {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [pw, setPw] = useState("");
  const [msg, setMsg] = useState("");
  const submit = async (e: any) => {
    e.preventDefault();
    if (mode === "forgot") {
      const r = await fetch(`${API_URL}/api/v1/auth/forgot-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) }).then((x) => x.json());
      setMsg(r.success ? `Reset token (dev): ${r.data.reset_token || "check email"}` : "Failed");
      if (r.success && r.data.reset_token) setToken(r.data.reset_token);
    } else {
      const r = await fetch(`${API_URL}/api/v1/auth/reset-password`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, new_password: pw }) }).then((x) => x.json());
      setMsg(r.success ? "Password reset. Please sign in." : r.error?.message || "Failed");
    }
  };
  return (
    <main className="max-w-md mx-auto px-4 py-16">
      <Link href="/" className="font-bold text-xl text-brand-700">PayFlow</Link>
      <h1 className="text-2xl font-bold mt-4">{mode === "forgot" ? "Forgot password" : "Reset password"}</h1>
      <form onSubmit={submit} className="card p-6 mt-4 space-y-4">
        {mode === "forgot" ? (
          <div><label className="label">Email</label><input className="input" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
        ) : (
          <><div><label className="label">Token</label><input className="input" value={token} onChange={(e) => setToken(e.target.value)} required /></div>
          <div><label className="label">New password</label><input type="password" className="input" value={pw} onChange={(e) => setPw(e.target.value)} required /></div></>
        )}
        <button className="btn-primary w-full">Submit</button>
        {msg && <p className="text-sm break-all">{msg}</p>}
        <p className="text-sm"><Link href="/reset-password" className="underline">Have a token? Reset</Link> · <Link href="/login" className="underline">Sign in</Link></p>
      </form>
    </main>
  );
}
