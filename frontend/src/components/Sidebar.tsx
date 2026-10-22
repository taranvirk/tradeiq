import { BarChart3, Bot, BriefcaseBusiness, ChartCandlestick, LayoutDashboard, ShieldCheck } from "lucide-react";
import { NavLink } from "react-router-dom";

import { Brand } from "./Brand";

const navigation = [
  { label: "Overview", path: "/dashboard", icon: LayoutDashboard },
  { label: "Markets", path: "/stocks", icon: ChartCandlestick },
  { label: "AI Signals", path: "/ai", icon: Bot },
  { label: "Backtests", path: "/backtests", icon: BarChart3 },
  { label: "Portfolio", path: "/portfolio", icon: BriefcaseBusiness },
  { label: "Risk Center", path: "/risk", icon: ShieldCheck },
] as const;

function Navigation({ mobile = false }: { mobile?: boolean }) {
  return <nav className={mobile ? "flex items-center justify-around" : "mt-10 flex flex-1 flex-col gap-1"} aria-label="Main navigation">{navigation.map((item) => { const Icon = item.icon; return <NavLink key={item.path} to={item.path} aria-label={item.label} className={({ isActive }) => mobile ? `grid min-w-12 place-items-center gap-1 px-1 py-2 text-[9px] ${isActive ? "text-accent" : "text-slate-500"}` : `flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition ${isActive ? "border-accent/15 bg-accent/10 font-medium text-accent" : "border-transparent text-slate-500 hover:bg-slate-800/50 hover:text-slate-300"}`}><Icon size={mobile ? 18 : 17} aria-hidden="true" /><span>{mobile && item.label === "AI Signals" ? "AI" : item.label}</span></NavLink>; })}</nav>;
}

export function Sidebar() {
  return <><aside className="hidden min-h-screen w-64 shrink-0 flex-col border-r border-line bg-[#080d17] px-4 py-6 lg:flex"><NavLink to="/dashboard" className="px-2"><Brand /></NavLink><Navigation /><div className="rounded-xl border border-line bg-panel/70 p-3"><div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-300"><ShieldCheck size={15} className="text-accent" />Risk-gated paper trading</div><p className="text-xs leading-5 text-slate-500">No live-money orders. Every simulated trade passes the independent risk engine.</p></div></aside><div className="fixed inset-x-0 bottom-0 z-50 border-t border-line bg-[#080d17]/95 px-1 backdrop-blur lg:hidden"><Navigation mobile /></div></>;
}
