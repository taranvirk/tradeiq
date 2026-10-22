import { useQuery } from "@tanstack/react-query";
import { Banknote, CircleDollarSign, TrendingUp, WalletCards } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorPanel, LoadingPanel } from "../components/QueryState";
import { StatCard } from "../components/StatCard";
import { apiMessage, getDashboard } from "../services/api";
import { useAuth } from "../auth/AuthState";

const money = (value: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);

export function Dashboard() {
  const { user } = useAuth();
  const query = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  if (query.isLoading) return <main className="page-shell"><LoadingPanel label="Loading your command center" /></main>;
  if (query.isError || !query.data) return <main className="page-shell"><ErrorPanel message={apiMessage(query.error)} /></main>;
  const { portfolio, opportunities, recent_orders: recentOrders } = query.data;

  return (
    <main className="page-shell">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div><div className="mb-2 flex items-center gap-2"><span className="demo-badge">{user?.is_demo ? "Demo portfolio" : "Paper portfolio"}</span><span className="text-xs text-slate-600">Risk engine active</span></div><h1 className="page-title">Portfolio command center</h1><p className="mt-2 text-sm text-slate-500">Market intelligence, strategy research, and safely simulated execution.</p></div>
        <a href={(import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000") + "/docs"} target="_blank" rel="noreferrer" className="rounded-lg border border-line bg-panel px-4 py-2 text-xs font-medium text-slate-300 hover:border-accent/40 hover:text-accent">Explore API docs</a>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Portfolio value" value={money(portfolio.equity)} change={`${portfolio.total_pnl >= 0 ? "+" : ""}${money(portfolio.total_pnl)} all time`} changeTone={portfolio.total_pnl >= 0 ? "positive" : "neutral"} icon={WalletCards} />
        <StatCard label="Today's P&L" value={`${portfolio.today_pnl >= 0 ? "+" : ""}${money(portfolio.today_pnl)}`} change={`Started with ${money(portfolio.starting_balance)}`} changeTone={portfolio.today_pnl >= 0 ? "positive" : "neutral"} icon={TrendingUp} />
        <StatCard label="Total return" value={`${portfolio.total_return >= 0 ? "+" : ""}${portfolio.total_return.toFixed(2)}%`} change="Since simulation start" changeTone="positive" icon={TrendingUp} />
        <StatCard label="Cash" value={money(portfolio.cash)} change={`${portfolio.market_exposure.toFixed(1)}% invested`} icon={Banknote} />
        <StatCard label="Buying power" value={money(portfolio.buying_power)} change={`${(portfolio.cash / portfolio.equity * 100).toFixed(1)}% available`} icon={CircleDollarSign} />
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,.8fr)]">
        <section className="panel-card p-5"><div className="mb-5"><p className="section-eyebrow">Portfolio performance</p><h2 className="mt-1 text-base font-semibold text-white">90-day equity curve</h2></div><div className="h-[310px]"><ResponsiveContainer width="100%" height="100%"><AreaChart data={portfolio.performance}><defs><linearGradient id="dashFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5eead4" stopOpacity={0.28} /><stop offset="100%" stopColor="#5eead4" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#1b2739" vertical={false} /><XAxis dataKey="date" hide /><YAxis domain={["dataMin - 200", "dataMax + 200"]} tick={{ fill: "#64748b", fontSize: 11 }} width={70} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} /><Tooltip contentStyle={{ background: "#0d1422", border: "1px solid #1b2739", borderRadius: 8 }} formatter={(value) => [money(Number(value)), "Equity"]} /><Area type="monotone" dataKey="value" stroke="#5eead4" fill="url(#dashFill)" strokeWidth={2} /></AreaChart></ResponsiveContainer></div></section>
        <section className="panel-card p-5"><p className="section-eyebrow">Current positions</p><div className="mt-4 space-y-2">{portfolio.positions.map((item) => <div key={item.symbol} className="rounded-lg border border-line bg-canvas/40 p-3"><div className="flex items-center justify-between"><div><strong className="font-mono text-sm text-white">{item.symbol}</strong><p className="text-[11px] text-slate-600">{item.quantity} shares · {money(item.market_value)}</p></div><span className={item.return_percent >= 0 ? "text-sm font-semibold text-positive" : "text-sm font-semibold text-negative"}>{item.return_percent >= 0 ? "+" : ""}{item.return_percent}%</span></div></div>)}</div></section>
      </div>
      <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(300px,.8fr)_minmax(0,1.7fr)]">
        <section className="panel-card p-5"><p className="section-eyebrow">AI opportunities</p><div className="mt-4 space-y-2">{opportunities.map((item) => <div key={item.symbol} className="flex items-center justify-between border-b border-line/60 py-3 last:border-0"><span className="font-mono text-sm font-semibold text-white">{item.symbol}</span><span className={item.signal === "BUY" ? "signal-buy" : item.signal === "SELL" ? "signal-sell" : "signal-hold"}>{item.signal}</span><span className="font-mono text-sm text-slate-300">{(item.probability_up * 100).toFixed(0)}%</span></div>)}</div></section>
        <section className="panel-card overflow-hidden"><div className="p-5"><p className="section-eyebrow">Recent order activity</p></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="border-y border-line bg-canvas/40 text-[10px] uppercase tracking-wider text-slate-600"><tr><th className="px-5 py-3">Symbol</th><th>Side</th><th>Qty</th><th>Fill</th><th>Status</th></tr></thead><tbody>{recentOrders.map((order) => <tr key={order.id} className="border-b border-line/60 last:border-0"><td className="px-5 py-4 font-mono font-semibold text-white">{order.symbol}</td><td className={order.side === "BUY" ? "text-positive" : "text-negative"}>{order.side}</td><td>{order.quantity}</td><td>{money(order.price)}</td><td><span className="rounded bg-slate-800 px-2 py-1 text-[10px] text-slate-300">{order.status}</span></td></tr>)}</tbody></table></div></section>
      </div>
      <p className="mt-5 text-center text-[11px] text-slate-700">Paper trading uses persisted simulated portfolio data. No live-money orders are submitted.</p>
    </main>
  );
}
