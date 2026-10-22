import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FlaskConical } from "lucide-react";
import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorPanel, LoadingPanel } from "../components/QueryState";
import { StockPicker } from "../components/StockPicker";
import { apiMessage, createBacktest, getBacktest, getBacktests } from "../services/api";

const strategies = [{ value: "moving_average", label: "Moving Average Crossover" }, { value: "rsi", label: "RSI Mean Reversion" }, { value: "ml", label: "Machine Learning Strategy" }];

export default function Backtests() {
  const [symbol, setSymbol] = useState("NVDA");
  const [strategy, setStrategy] = useState("moving_average");
  const [capital, setCapital] = useState(10000);
  const [selectedId, setSelectedId] = useState<number>();
  const client = useQueryClient();
  const list = useQuery({ queryKey: ["backtests"], queryFn: getBacktests });
  const effectiveId = selectedId ?? list.data?.[0]?.id;
  const detail = useQuery({ queryKey: ["backtest", effectiveId], queryFn: () => getBacktest(effectiveId!), enabled: Boolean(effectiveId) });
  const run = useMutation({ mutationFn: () => createBacktest({ symbol, strategy, starting_capital: capital, position_size: 0.8, commission: 1, slippage: 0.0005 }), onSuccess: (data) => { client.invalidateQueries({ queryKey: ["backtests"] }); client.setQueryData(["backtest", data.id], data); setSelectedId(data.id); } });
  if (list.isLoading) return <main className="page-shell"><LoadingPanel label="Loading backtest laboratory" /></main>;
  if (list.isError) return <main className="page-shell"><ErrorPanel message={apiMessage(list.error)} /></main>;
  const result = detail.data;
  const chart = result?.equity_curve?.map((point, index) => ({ ...point, benchmark: result.benchmark_curve?.[index]?.value })) ?? [];

  return (
    <main className="page-shell">
      <div className="mb-7"><span className="demo-badge">No look-ahead · costs included</span><h1 className="page-title mt-3">Strategy laboratory</h1><p className="mt-2 text-sm text-slate-500">Test reproducible signals against buy-and-hold using chronological market data.</p></div>
      <div className="grid gap-4 xl:grid-cols-[340px_minmax(0,1fr)]">
        <div className="space-y-4"><form onSubmit={(event) => { event.preventDefault(); run.mutate(); }} className="panel-card space-y-4 p-5"><div className="flex items-center gap-3"><FlaskConical className="text-accent" size={18} /><h2 className="font-semibold text-white">New backtest</h2></div><StockPicker value={symbol} onChange={setSymbol} label="Stock to backtest" /><label className="block text-xs text-slate-500">Strategy<select value={strategy} onChange={(event) => setStrategy(event.target.value)} className="control mt-2 w-full">{strategies.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label className="block text-xs text-slate-500">Starting capital<input type="number" min="1000" value={capital} onChange={(event) => setCapital(Number(event.target.value))} className="control mt-2 w-full font-mono" /></label><div className="grid grid-cols-2 gap-3"><div className="rounded-lg bg-canvas/50 p-3"><p className="text-[10px] uppercase text-slate-600">Commission</p><p className="mt-1 font-mono text-xs text-white">$1.00</p></div><div className="rounded-lg bg-canvas/50 p-3"><p className="text-[10px] uppercase text-slate-600">Slippage</p><p className="mt-1 font-mono text-xs text-white">5 bps</p></div></div><button type="submit" className="primary-button w-full" disabled={run.isPending}>{run.isPending ? `Running ${symbol} simulation…` : `Run ${symbol} backtest`}</button>{run.isError && <p className="text-xs text-negative">{apiMessage(run.error)}</p>}</form><section className="panel-card p-3"><p className="section-eyebrow px-2 py-2">Saved research</p>{list.data?.map((item) => <button key={item.id} onClick={() => setSelectedId(item.id)} className={`mb-1 w-full rounded-lg border p-3 text-left ${effectiveId === item.id ? "border-accent/20 bg-accent/10" : "border-transparent hover:bg-slate-800/40"}`}><div className="flex justify-between"><span className="font-mono text-sm font-semibold text-white">{item.symbol}</span><span className={item.metrics.total_return >= 0 ? "text-xs text-positive" : "text-xs text-negative"}>{item.metrics.total_return >= 0 ? "+" : ""}{item.metrics.total_return}%</span></div><p className="mt-1 text-[10px] text-slate-600">{item.strategy.replaceAll("_", " ")} · #{item.id}</p></button>)}</section></div>
        {detail.isLoading ? <LoadingPanel label="Loading result" /> : detail.isError ? <ErrorPanel message={apiMessage(detail.error)} /> : result ? <div className="space-y-4"><section className="panel-card p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="section-eyebrow">Completed research</p><h2 className="mt-2 font-mono text-xl font-semibold text-white">{result.symbol} · {result.strategy.replaceAll("_", " ")}</h2><p className="mt-1 text-xs text-slate-600">{result.start_date} → {result.end_date}</p></div><span className="signal-buy">{result.status}</span></div><div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">{[["Total return", `${result.metrics.total_return}%`], ["SPY benchmark", `${result.metrics.benchmark_return}%`], ["Sharpe", result.metrics.sharpe_ratio], ["Max drawdown", `${result.metrics.max_drawdown}%`], ["Sortino", result.metrics.sortino_ratio], ["Win rate", `${result.metrics.win_rate}%`], ["Profit factor", result.metrics.profit_factor], ["Trades", result.metrics.trade_count]].map(([label, value]) => <div key={label} className="rounded-lg border border-line bg-canvas/40 p-3"><p className="text-[10px] uppercase tracking-wider text-slate-600">{label}</p><p className="mt-2 font-mono text-base text-white">{value}</p></div>)}</div></section><section className="panel-card p-5"><p className="section-eyebrow">Equity curve</p><h3 className="mt-1 font-semibold text-white">Strategy vs. benchmark</h3><div className="mt-5 h-[360px]"><ResponsiveContainer width="100%" height="100%"><LineChart data={chart}><CartesianGrid stroke="#1b2739" vertical={false} /><XAxis dataKey="date" hide /><YAxis domain={["auto", "auto"]} tick={{ fill: "#64748b", fontSize: 11 }} width={68} /><Tooltip contentStyle={{ background: "#0d1422", border: "1px solid #1b2739" }} /><Legend /><Line name="Strategy" dataKey="value" stroke="#5eead4" dot={false} strokeWidth={2} /><Line name="SPY benchmark" dataKey="benchmark" stroke="#64748b" dot={false} strokeWidth={1.5} /></LineChart></ResponsiveContainer></div></section></div> : null}
      </div>
    </main>
  );
}
