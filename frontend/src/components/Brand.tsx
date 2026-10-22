import { Activity } from "lucide-react";

export function Brand() {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-10 w-10 place-items-center rounded-xl border border-accent/30 bg-accent/10 text-accent shadow-glow">
        <Activity size={21} strokeWidth={2.2} aria-hidden="true" />
      </div>
      <div>
        <p className="text-lg font-semibold tracking-tight text-white">TradeIQ</p>
        <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-slate-500">Market intelligence</p>
      </div>
    </div>
  );
}

