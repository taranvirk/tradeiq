import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ErrorPanel, LoadingPanel } from "../components/QueryState";
import { apiMessage, getTradingSettings, updateTradingSettings } from "../services/api";
import type { PaperAccount } from "../types/api";

export default function TradingSettings() {
  const query = useQuery({ queryKey: ["trading-settings"], queryFn: getTradingSettings });
  if (query.isLoading) return <main className="page-shell"><LoadingPanel label="Loading trading settings" /></main>;
  if (query.isError || !query.data) return <main className="page-shell"><ErrorPanel message={apiMessage(query.error)} /></main>;
  return <TradingSettingsForm key={query.data.id} account={query.data} />;
}

function TradingSettingsForm({ account }: { account: PaperAccount }) {
  const client = useQueryClient();
  const [form, setForm] = useState({ risk_per_trade: account.risk_per_trade, max_position_size: account.max_position_size, max_daily_loss: account.max_daily_loss, default_order_amount: account.default_order_amount, ai_auto_trade_enabled: account.ai_auto_trade_enabled });
  const mutation = useMutation({ mutationFn: () => updateTradingSettings(form), onSuccess: () => client.invalidateQueries({ queryKey: ["trading-settings"] }) });
  const change = (key: keyof typeof form, value: number | boolean) => setForm((current) => ({ ...current, [key]: value }));
  const submit = (event: FormEvent) => { event.preventDefault(); mutation.mutate(); };
  return <main className="page-shell"><div className="mb-7"><p className="section-eyebrow">Paper trading</p><h1 className="page-title mt-2">Trading settings</h1><p className="mt-2 text-sm text-slate-500">Personalize sizing defaults within TradeIQ's hard safety limits.</p></div><form onSubmit={submit} className="panel-card max-w-2xl p-6"><div className="grid gap-4 sm:grid-cols-2"><PercentField label="Risk per trade" value={form.risk_per_trade} min={0.1} max={5} onChange={(value) => change("risk_per_trade", value / 100)} /><PercentField label="Maximum position size" value={form.max_position_size} min={1} max={25} onChange={(value) => change("max_position_size", value / 100)} /><PercentField label="Maximum daily loss" value={form.max_daily_loss} min={0.5} max={5} onChange={(value) => change("max_daily_loss", value / 100)} /><label className="text-sm text-slate-400">Default order amount<input type="number" min="1" max="1000000" step="1" className="control mt-2 w-full" value={form.default_order_amount} onChange={(event) => change("default_order_amount", Number(event.target.value))} /></label></div><label className="mt-5 flex items-center justify-between rounded-lg border border-line bg-canvas/50 p-4"><div><span className="text-sm font-medium text-white">AI auto-trade</span><p className="mt-1 text-xs text-slate-600">Stored for future paper automation; all hard risk gates still apply.</p></div><input type="checkbox" checked={form.ai_auto_trade_enabled} onChange={(event) => change("ai_auto_trade_enabled", event.target.checked)} className="h-4 w-4 accent-cyan-300" /></label>{mutation.isError && <p className="mt-4 text-sm text-negative">{apiMessage(mutation.error)}</p>}{mutation.isSuccess && <p className="mt-4 text-sm text-positive">Trading settings saved.</p>}<button className="primary-button mt-5" disabled={mutation.isPending}>Save settings</button></form></main>;
}

function PercentField({ label, value, min, max, onChange }: { label: string; value: number; min: number; max: number; onChange: (value: number) => void }) { return <label className="text-sm text-slate-400">{label}<div className="relative mt-2"><input type="number" min={min} max={max} step="0.1" className="control w-full pr-9" value={value * 100} onChange={(event) => onChange(Number(event.target.value))} /><span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600">%</span></div></label>; }
