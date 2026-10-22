const opportunities = [
  { symbol: "NVDA", name: "NVIDIA", signal: "BUY", confidence: 72, change: "+2.84%" },
  { symbol: "AAPL", name: "Apple", signal: "BUY", confidence: 68, change: "+1.42%" },
  { symbol: "MSFT", name: "Microsoft", signal: "BUY", confidence: 65, change: "+0.61%" },
  { symbol: "GOOG", name: "Alphabet", signal: "HOLD", confidence: 55, change: "-0.18%" },
];

export function Opportunities() {
  return (
    <section className="panel-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <div>
          <p className="section-eyebrow">AI opportunities</p>
          <h2 className="mt-1 text-base font-semibold text-white">Signal watchlist</h2>
        </div>
        <span className="demo-badge">Demo data</span>
      </div>
      <div className="divide-y divide-line/70">
        {opportunities.map((item) => (
          <div key={item.symbol} className="grid grid-cols-[1fr_auto] items-center gap-4 px-5 py-4 sm:grid-cols-[1fr_78px_90px]">
            <div>
              <p className="text-sm font-semibold text-slate-100">{item.symbol}</p>
              <p className="mt-0.5 text-xs text-slate-600">{item.name}</p>
            </div>
            <div className="hidden sm:block">
              <span className={item.signal === "BUY" ? "signal-buy" : "signal-hold"}>{item.signal}</span>
            </div>
            <div className="text-right">
              <p className="font-mono text-sm font-medium text-white">{item.confidence}%</p>
              <p className={item.change.startsWith("+") ? "mt-0.5 text-xs text-positive" : "mt-0.5 text-xs text-negative"}>{item.change}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

