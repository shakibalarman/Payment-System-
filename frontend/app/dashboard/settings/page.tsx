"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../lib/api";
import { RequireRole } from "../../../lib/auth";
import { Shell, MERCHANT_NAV } from "../../../components/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("pf_access")}` });

function SettingsInner() {
  const { data: me } = useQuery({ queryKey: ["mme"], queryFn: () => api("/api/v1/merchants/me") });
  const [f, setF] = useState({ business_name: "", business_type: "Retail", owner_name: "", phone: "", email: "", address: "", trade_license: "", tin: "", nid_passport: "", bank_account: "", bank_name: "" });
  const [msg, setMsg] = useState("");
  const save = async (kyc: boolean) => {
    const r = await fetch(`${API}${kyc ? "/api/v1/merchants/kyc" : "/api/v1/merchants/me"}`, { method: kyc ? "POST" : "PUT", headers: H(), body: JSON.stringify({ ...f, business_name: f.business_name || me?.business_name || "My Business" }) }).then((x) => x.json());
    setMsg(r.success ? (kyc ? "KYC submitted for review." : "Profile saved.") : r.error?.message);
  };
  return (
    <Shell nav={MERCHANT_NAV}>
      <h1 className="text-2xl font-bold mb-4">Settings · Profile · KYC</h1>
      <p className="text-sm mb-3">KYC status: <strong>{me?.kyc_status}</strong> · Fee: {me?.fee_percent}%</p>
      <div className="card p-5 grid sm:grid-cols-2 gap-3">
        {[["business_name", "Business name"], ["business_type", "Business type"], ["owner_name", "Owner name"], ["phone", "Phone"], ["email", "Email"], ["address", "Address"], ["trade_license", "Trade license"], ["tin", "TIN"], ["nid_passport", "NID/Passport"], ["bank_account", "Bank account"], ["bank_name", "Bank name"]].map(([k, label]) => (
          <div key={k}><label className="label">{label}</label><input className="input" value={(f as any)[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></div>
        ))}
      </div>
      <div className="flex gap-2 mt-3">
        <button className="btn-secondary" onClick={() => save(false)}>Save profile</button>
        <button className="btn-primary" onClick={() => save(true)}>Submit KYC</button>
      </div>
      {msg && <p className="text-sm mt-2">{msg}</p>}
    </Shell>
  );
}

export default function SettingsPage() {
  return <RequireRole roles={["merchant"]}><SettingsInner /></RequireRole>;
}
