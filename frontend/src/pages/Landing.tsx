import { BarChart3, Bot, ChartCandlestick, LineChart, ShieldCheck, WalletCards } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Brand } from "../components/Brand";
import { apiMessage } from "../services/api";
import { useAuth } from "../auth/AuthState";
import { useState } from "react";

const features = [
  [Bot, "AI market signals", "Explainable directional predictions built from technical and market features."],
  [BarChart3, "Strategy backtesting", "Compare systematic strategies against a buy-and-hold benchmark."],
  [ChartCandlestick, "Market intelligence", "Validated price history, indicators, watchlists, and scanner results."],
  [WalletCards, "Paper trading", "Practice with persistent simulated cash and fractional-share orders."],
  [LineChart, "Portfolio analytics", "Track equity, attribution, drawdown, positions, and realized performance."],
  [ShieldCheck, "Risk management", "Every paper order passes buying-power, exposure, and position limits."],
] as const;

export default function Landing() {
  const { viewDemo } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const demo = async () => {
    setLoading(true); setError("");
    try { await viewDemo(); navigate("/dashboard"); } catch (cause) { setError(apiMessage(cause)); } finally { setLoading(false); }
  };
  return <div className="min-h-screen bg-canvas text-slate-300">
    <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-6"><Brand /><nav className="flex items-center gap-3"><Link to="/login" className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white">Sign in</Link><Link to="/signup" className="primary-button">Start paper trading</Link></nav></header>
    <main>
      <section className="mx-auto grid max-w-7xl gap-12 px-5 pb-20 pt-16 lg:grid-cols-[1.15fr_.85fr] lg:items-center lg:pt-24">
        <div><span className="demo-badge">No real money · production-style simulation</span><h1 className="mt-6 max-w-4xl text-5xl font-semibold leading-[1.05] tracking-[-0.04em] text-white sm:text-6xl">AI-powered market analysis and algorithmic paper trading.</h1><p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">Analyze markets. Backtest strategies. Simulate trades. Measure performance—all in one risk-controlled research platform.</p><div className="mt-9 flex flex-wrap gap-3"><Link to="/signup" className="primary-button px-6 py-3">Create free account</Link><button type="button" disabled={loading} onClick={demo} className="rounded-lg border border-line bg-panel px-6 py-3 text-sm font-semibold text-white hover:border-accent/40">{loading ? "Opening demo…" : "View demo portfolio"}</button></div>{error && <p className="mt-3 text-sm text-negative">{error}</p>}</div>
        <div className="panel-card relative overflow-hidden p-6"><div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(94,234,212,.12),transparent_45%)]" /><div className="relative"><div className="flex items-center justify-between"><span className="section-eyebrow">Portfolio intelligence</span><span className="signal-buy">BUY</span></div><div className="mt-8 grid grid-cols-2 gap-3"><div className="rounded-xl border border-line bg-canvas/70 p-4"><p className="text-xs text-slate-500">Paper equity</p><p className="mt-2 font-mono text-2xl text-white">$25,842.16</p><p className="mt-1 text-xs text-positive">+3.37% this month</p></div><div className="rounded-xl border border-line bg-canvas/70 p-4"><p className="text-xs text-slate-500">Buying power</p><p className="mt-2 font-mono text-2xl text-white">$11,420.00</p><p className="mt-1 text-xs text-slate-600">Risk limits active</p></div></div><div className="mt-4 flex h-48 items-end gap-2 rounded-xl border border-line bg-canvas/70 p-5">{[28,36,32,48,44,63,58,76,69,88,82,96].map((height, index) => <div key={index} className="flex-1 rounded-t bg-gradient-to-t from-cyan-950 to-accent" style={{ height: `${height}%`, opacity: .45 + index / 24 }} />)}</div></div></div>
      </section>
      <section className="border-t border-line bg-[#080d17]"><div className="mx-auto max-w-7xl px-5 py-20"><div className="max-w-2xl"><p className="section-eyebrow">Research to execution</p><h2 className="mt-3 text-3xl font-semibold text-white">A complete paper-trading workflow</h2></div><div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">{features.map(([Icon, title, description]) => <article key={title} className="panel-card p-5"><div className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent"><Icon size={20} /></div><h3 className="mt-5 font-semibold text-white">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{description}</p></article>)}</div></div></section>
    </main>
  </div>;
}
