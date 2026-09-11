"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";

type User = { id: string; email: string; role: string; full_name: string; is_verified: boolean };
type Ctx = { user: User | null; loading: boolean; login: (email: string, pw: string) => Promise<void>; register: (v: any) => Promise<void>; logout: () => void };

const AuthCtx = createContext<Ctx>({ user: null, loading: true, login: async () => {}, register: async () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const t = localStorage.getItem("pf_access");
    if (!t) return setLoading(false);
    api("/api/v1/users/me").then(setUser).catch(() => localStorage.removeItem("pf_access")).finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const d = await api("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    localStorage.setItem("pf_access", d.access_token);
    localStorage.setItem("pf_refresh", d.refresh_token);
    setUser(d.user);
    router.push(d.user.role === "admin" ? "/admin" : d.user.role === "merchant" ? "/dashboard" : "/customer");
  };
  const register = async (v: any) => {
    const d = await api("/api/v1/auth/register", { method: "POST", body: JSON.stringify(v) });
    localStorage.setItem("pf_access", d.access_token);
    localStorage.setItem("pf_refresh", d.refresh_token);
    setUser(d.user);
    router.push(d.user.role === "merchant" ? "/dashboard" : "/customer");
  };
  const logout = () => {
    const r = localStorage.getItem("pf_refresh");
    if (r) api("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token: r }) }).catch(() => {});
    localStorage.removeItem("pf_access");
    localStorage.removeItem("pf_refresh");
    setUser(null);
    router.push("/login");
  };
  return <AuthCtx.Provider value={{ user, loading, login, register, logout }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);

export function RequireRole({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && (!user || !roles.includes(user.role))) router.push("/login");
  }, [user, loading]);
  if (loading) return <div className="p-8">Loading…</div>;
  if (!user || !roles.includes(user.role)) return <div className="p-8">403 — Forbidden for your role.</div>;
  return <>{children}</>;
}
