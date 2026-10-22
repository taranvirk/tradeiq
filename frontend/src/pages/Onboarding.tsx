import { useState } from "react";
import { CircleDollarSign, ShieldCheck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthState";
import { apiMessage, createPaperAccount } from "../services/api";

const presets = [1000, 5000, 10000, 25000, 50000, 100000];

export default function Onboarding() {
  const { user, refreshUser, signOut } = useAuth(); const navigate = useNavigate();
  const [amount, setAmount] = useState(10000); const [custom, setCustom] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const selected = custom ? Number(custom) : amount;
  const create = async () => { setError(""); if (!Number.isFinite(selected) || selected < 100 || selected > 10_000_000) { setError("Choose an amount between $100 and $10,000,000."); return; } setLoading(true); try { await createPaperAccount(selected); await refreshUser(); navigate("/dashboard", { replace: true }); } catch (cause) { setError(apiMessage(cause)); } finally { setLoading(false); } };
  return <div className="grid min-h-screen place-items-center bg-canvas px-4 py-10"><section className="panel-card w-full max-w-2xl p-6 sm:p-9"><div className="flex items-start justify-between gap-4"><div><span className="demo-badge">Simulated funds only</span><h1 className="mt-4 text-3xl font-semibold text-white">Welcome, {user?.first_name}</h1><p className="mt-2 text-slate-500">Choose the starting balance for your paper trading portfolio. No real funds are deposited.</p></div><div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent"><ShieldCheck /></div></div><h2 className="mt-8 text-sm font-semibold text-white">Choose your starting paper balance</h2><div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">{presets.map((value) => <button key={value} type="button" onClick={() => { setAmount(value); setCustom(""); }} className={`rounded-lg border px-4 py-3 font-mono text-sm ${!custom && amount === value ? "border-accent bg-accent/10 text-accent" : "border-line text-slate-400 hover:border-slate-600"}`}>${value.toLocaleString()}</button>)}</div><label className="mt-5 block text-sm text-slate-400">Custom amount<div className="relative mt-2"><CircleDollarSign className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={17} /><input type="number" min="100" max="10000000" step="100" value={custom} onChange={(event) => setCustom(event.target.value)} placeholder="15,000" className="control w-full pl-10" /></div></label><div className="mt-5 rounded-lg border border-line bg-canvas/60 p-4 text-sm"><span className="text-slate-500">Starting balance</span><strong className="float-right font-mono text-white">${(Number.isFinite(selected) ? selected : 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></div>{error && <p className="mt-4 text-sm text-negative">{error}</p>}<button type="button" onClick={create} disabled={loading} className="primary-button mt-5 w-full">{loading ? "Creating portfolio…" : "Create paper portfolio"}</button><button type="button" onClick={() => void signOut()} className="mt-3 w-full text-xs text-slate-600 hover:text-slate-400">Sign out</button></section></div>;
}
