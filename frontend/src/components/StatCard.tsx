import type { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  change?: string;
  changeTone?: "positive" | "neutral";
  icon: LucideIcon;
}

export function StatCard({ label, value, change, changeTone = "neutral", icon: Icon }: StatCardProps) {
  return (
    <article className="panel-card group p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">{label}</p>
          <p className="mt-3 font-mono text-2xl font-semibold tracking-tight text-white">{value}</p>
        </div>
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-slate-800/70 text-slate-400 transition-colors group-hover:text-accent">
          <Icon size={18} aria-hidden="true" />
        </div>
      </div>
      {change && (
        <p className={changeTone === "positive" ? "mt-3 text-xs font-medium text-positive" : "mt-3 text-xs text-slate-500"}>
          {change}
        </p>
      )}
    </article>
  );
}

