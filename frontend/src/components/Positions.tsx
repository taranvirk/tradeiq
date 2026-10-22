const positions = [
  { symbol: "AAPL", shares: "12 shares", value: "$2,814.48", returnValue: "+3.20%" },
  { symbol: "MSFT", shares: "6 shares", value: "$2,530.92", returnValue: "+1.40%" },
  { symbol: "NVDA", shares: "18 shares", value: "$3,262.14", returnValue: "-0.80%" },
];

export function Positions() {
  return (
    <section className="panel-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <div>
          <p className="section-eyebrow">Allocation</p>
          <h2 className="mt-1 text-base font-semibold text-white">Current positions</h2>
        </div>
        <span className="demo-badge">Demo data</span>
      </div>
      <div className="divide-y divide-line/70">
        {positions.map((position) => (
          <div key={position.symbol} className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-5">
            <div className="flex items-center gap-3">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-slate-800 font-mono text-xs font-semibold text-slate-200">
                {position.symbol.slice(0, 2)}
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-100">{position.symbol}</p>
                <p className="mt-0.5 text-xs text-slate-600">{position.shares}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-mono text-sm text-slate-200">{position.value}</p>
              <p className={position.returnValue.startsWith("+") ? "mt-0.5 text-xs text-positive" : "mt-0.5 text-xs text-negative"}>
                {position.returnValue}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

