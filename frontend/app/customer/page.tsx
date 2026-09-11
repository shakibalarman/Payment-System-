"use client";
import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api, fmtMoney, statusBadge } from "../../lib/api";
import { RequireRole, useAuth } from "../../lib/auth";
import { FALLBACK_PRODUCTS, Product, unitPrice } from "../../lib/products";

type Sel = { color: string; size: string; storage: string; ram: string; qty: number; method: string };

const DEFAULT_SEL: Sel = { color: "", size: "", storage: "", ram: "", qty: 1, method: "card" };

function CustomerInner() {
  const { logout, user } = useAuth();
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [cat, setCat] = useState("All");
  const [sort, setSort] = useState("pop");
  const [active, setActive] = useState<Product | null>(null);
  const [sel, setSel] = useState<Sel>(DEFAULT_SEL);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<{ id: string; name: string } | null>(null);
  const [tab, setTab] = useState<"shop" | "orders">("shop");

  const { data: remote } = useQuery({ queryKey: ["shop-products"], queryFn: () => api("/api/v1/shop/products") });
  const { data: orders } = useQuery({ queryKey: ["cpay"], queryFn: () => api("/api/v1/customer/payments") });

  const products: Product[] = remote?.length ? remote : FALLBACK_PRODUCTS;

  const cats = useMemo(() => ["All", ...Array.from(new Set(products.map((p) => p.category)))], [products]);

  const list = useMemo(() => {
    let l = products.filter(
      (p) => (cat === "All" || p.category === cat) && (p.name + p.description).toLowerCase().includes(query.toLowerCase())
    );
    if (sort === "low") l = [...l].sort((a, b) => a.base_price - b.base_price);
    if (sort === "high") l = [...l].sort((a, b) => b.base_price - a.base_price);
    if (sort === "pop") l = [...l].sort((a, b) => b.rating - a.rating);
    return l;
  }, [products, cat, query, sort]);

  const open = (p: Product) => {
    setActive(p);
    setSel({ ...DEFAULT_SEL, color: p.colors?.[0] || "", size: p.sizes?.[1] || p.sizes?.[0] || "", storage: p.storages?.[0] || "", ram: p.rams?.[0] || "" });
    setErr("");
    setDone(null);
  };

  const previewUnit = active ? unitPrice(active, sel) : 0;
  const previewFee = Math.round(previewUnit * sel.qty * 0.015);
  const previewTotal = previewUnit * sel.qty;

  const buy = async () => {
    if (!active) return;
    setBusy(true);
    setErr("");
    try {
      const order = await api("/api/v1/shop/buy", {
        method: "POST",
        headers: { "Idempotency-Key": `shop-${active.id}-${Date.now()}` },
        body: JSON.stringify({
          product_id: active.id,
          quantity: sel.qty,
          color: sel.color,
          size: sel.size,
          storage: sel.storage,
          ram: sel.ram,
          payment_method: sel.method,
        }),
      });
      await api(`/api/v1/shop/pay/${order.id}`, {
        method: "POST",
        body: JSON.stringify({ outcome: "SUCCESS", payment_method: sel.method }),
      });
      setDone({ id: order.id, name: active.name });
      qc.invalidateQueries({ queryKey: ["cpay"] });
    } catch (e: any) {
      setErr(e.message || "Payment failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-wrap gap-3 justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold">PayFlow Shop</h1>
          <p className="text-sm text-slate-500">Signed in as {user?.email} · <span className="font-bold text-amber-700">DEMO — no real money</span></p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setTab("shop")} className={tab === "shop" ? "btn-primary text-sm" : "btn-secondary text-sm"}>Shop</button>
          <button onClick={() => setTab("orders")} className={tab === "orders" ? "btn-primary text-sm" : "btn-secondary text-sm"}>My Orders ({(orders || []).length})</button>
          <button className="btn-secondary text-sm" onClick={logout}>Logout</button>
        </div>
      </div>

      {tab === "orders" ? (
        <section className="mt-6">
          <div className="table-wrap"><table className="data">
            <thead><tr><th>Order / Description</th><th>Amount</th><th>Status</th><th>Receipt</th></tr></thead>
            <tbody>
              {(orders || []).map((p: any) => (
                <tr key={p.id}>
                  <td>{p.description}</td>
                  <td>{fmtMoney(p.amount, p.currency)}</td>
                  <td><span className={`px-2 py-0.5 rounded text-xs ${statusBadge(p.status)}`}>{p.status}</span></td>
                  <td><Link className="underline" href={`/receipt/${p.id}`}>Receipt</Link></td>
                </tr>
              ))}
            </tbody>
          </table></div>
          {(orders || []).length === 0 && <p className="text-sm text-slate-500 mt-3">No orders yet — go to Shop and buy something.</p>}
        </section>
      ) : (
        <>
          {/* Filters */}
          <div className="card p-4 mt-6 flex flex-wrap gap-3 items-center">
            <input aria-label="Search products" className="input max-w-xs" placeholder="Search t-shirt, laptop, mobile…" value={query} onChange={(e) => setQuery(e.target.value)} />
            <div className="flex gap-2" role="tablist" aria-label="Categories">
              {cats.map((c) => (
                <button key={c} onClick={() => setCat(c)} className={`px-3 py-1.5 rounded-xl text-sm border ${cat === c ? "bg-slate-900 text-white" : "bg-white"}`}>{c}</button>
              ))}
            </div>
            <select aria-label="Sort" className="input max-w-[180px] ml-auto" value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="pop">Most popular</option>
              <option value="low">Price: low → high</option>
              <option value="high">Price: high → low</option>
            </select>
          </div>

          {/* Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
            {list.map((p) => (
              <article key={p.id} className="card p-5 flex flex-col">
                <div className="text-5xl" aria-hidden>{p.emoji}</div>
                <p className="text-xs text-slate-500 mt-3">{p.category} · ⭐ {p.rating} · {p.stock} in stock</p>
                <h2 className="font-bold mt-1">{p.name}</h2>
                <p className="text-sm text-slate-600 mt-1 line-clamp-2">{p.description}</p>
                <p className="text-xl font-extrabold mt-2">{fmtMoney(p.base_price, p.currency)}</p>
                <button className="btn-primary w-full mt-3 text-sm" onClick={() => open(p)}>Buy Now</button>
              </article>
            ))}
          </div>
          {list.length === 0 && <p className="text-sm text-slate-500 mt-6">No products match “{query}”.</p>}
        </>
      )}

      {/* Detail modal */}
      {active && (
        <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center p-4 z-50" role="dialog" aria-modal="true" aria-label={active.name}>
          <div className="card p-6 w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-5xl">{active.emoji}</div>
                <h2 className="text-xl font-bold mt-2">{active.name}</h2>
                <p className="text-sm text-slate-600">{active.description}</p>
              </div>
              <button aria-label="Close" className="btn-secondary text-sm px-3 py-1" onClick={() => setActive(null)}>✕</button>
            </div>

            {done ? (
              <div className="mt-4 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                <p className="font-bold text-emerald-800">✅ Payment successful!</p>
                <p className="text-sm mt-1">{done.name} — order <code>{done.id.slice(0, 8)}</code></p>
                <div className="flex gap-2 mt-3">
                  <Link href={`/receipt/${done.id}`} className="btn-primary text-sm">View Receipt</Link>
                  <button className="btn-secondary text-sm" onClick={() => { setActive(null); setTab("orders"); }}>My Orders</button>
                </div>
              </div>
            ) : (
              <>
                {active.colors && (
                  <div className="mt-4"><label className="label" htmlFor="opt-color">Color</label>
                    <select id="opt-color" className="input" value={sel.color} onChange={(e) => setSel({ ...sel, color: e.target.value })}>
                      {active.colors.map((c) => <option key={c}>{c}</option>)}
                    </select></div>
                )}
                {active.sizes && (
                  <div className="mt-3"><span className="label">Size</span>
                    <div className="flex flex-wrap gap-2">
                      {active.sizes.map((s) => (
                        <button key={s} onClick={() => setSel({ ...sel, size: s })} className={`px-3 py-1.5 rounded-xl text-sm border ${sel.size === s ? "bg-slate-900 text-white" : "bg-white"}`}>{s}</button>
                      ))}
                    </div></div>
                )}
                {active.storages && (
                  <div className="mt-3"><label className="label" htmlFor="opt-storage">Storage</label>
                    <select id="opt-storage" className="input" value={sel.storage} onChange={(e) => setSel({ ...sel, storage: e.target.value })}>
                      {active.storages.map((c) => <option key={c}>{c}</option>)}
                    </select></div>
                )}
                {active.rams && (
                  <div className="mt-3"><label className="label" htmlFor="opt-ram">RAM</label>
                    <select id="opt-ram" className="input" value={sel.ram} onChange={(e) => setSel({ ...sel, ram: e.target.value })}>
                      {active.rams.map((c) => <option key={c}>{c}</option>)}
                    </select></div>
                )}
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <div><label className="label" htmlFor="opt-qty">Quantity</label>
                    <input id="opt-qty" type="number" min={1} max={10} className="input" value={sel.qty} onChange={(e) => setSel({ ...sel, qty: Math.max(1, Math.min(10, Number(e.target.value) || 1)) })} /></div>
                  <div><span className="label">Pay with</span>
                    <div className="flex gap-2 text-sm">
                      {(["card", "mobile_banking", "bank_transfer"] as const).map((m) => (
                        <label key={m} className={`px-2 py-1.5 border rounded-xl cursor-pointer ${sel.method === m ? "bg-slate-900 text-white" : ""}`}>
                          <input type="radio" className="sr-only" checked={sel.method === m} onChange={() => setSel({ ...sel, method: m })} />{m.replace("_", " ")}
                        </label>
                      ))}
                    </div></div>
                </div>

                <dl className="text-sm mt-4 space-y-1 bg-slate-50 rounded-xl p-3">
                  <div className="flex justify-between"><dt>Unit price</dt><dd>{fmtMoney(previewUnit, active.currency)}</dd></div>
                  <div className="flex justify-between"><dt>Qty</dt><dd>× {sel.qty}</dd></div>
                  <div className="flex justify-between"><dt>Platform fee (1.5%)</dt><dd>{fmtMoney(previewFee, active.currency)}</dd></div>
                  <div className="flex justify-between font-bold text-base"><dt>Total</dt><dd>{fmtMoney(previewTotal, active.currency)}</dd></div>
                </dl>
                {err && <p role="alert" className="text-sm text-rose-600 mt-2">{err}</p>}
                <button className="btn-primary w-full mt-4" disabled={busy} onClick={buy}>{busy ? "Processing payment…" : `Pay ${fmtMoney(previewTotal, active.currency)}`}</button>
                <p className="text-xs text-slate-500 mt-2">DEMO / MOCK payment — no real money. Idempotent, receipt + wallet updated on backend.</p>
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

export default function CustomerPage() {
  return <RequireRole roles={["customer"]}><CustomerInner /></RequireRole>;
}
