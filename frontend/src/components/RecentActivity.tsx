const trades = [
  { time: "10:42 AM", symbol: "NVDA", side: "BUY", quantity: "4", price: "$181.23", status: "Filled" },
  { time: "Yesterday", symbol: "MSFT", side: "BUY", quantity: "2", price: "$421.82", status: "Filled" },
  { time: "Sep 15", symbol: "TSLA", side: "SELL", quantity: "3", price: "$243.10", status: "Filled" },
];

export function RecentActivity() {
  return (
    <section className="panel-card overflow-hidden">
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <div>
          <p className="section-eyebrow">Execution log</p>
          <h2 className="mt-1 text-base font-semibold text-white">Recent activity</h2>
        </div>
        <span className="demo-badge">Demo data</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[620px] text-left text-sm">
          <thead className="border-b border-line bg-[#0a101c] text-[10px] uppercase tracking-[0.14em] text-slate-600">
            <tr>
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Symbol</th>
              <th className="px-5 py-3 font-medium">Side</th>
              <th className="px-5 py-3 font-medium">Quantity</th>
              <th className="px-5 py-3 font-medium">Fill price</th>
              <th className="px-5 py-3 text-right font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line/70">
            {trades.map((trade) => (
              <tr key={trade.time + trade.symbol} className="text-slate-300">
                <td className="px-5 py-4 text-xs text-slate-500">{trade.time}</td>
                <td className="px-5 py-4 font-semibold text-white">{trade.symbol}</td>
                <td className={trade.side === "BUY" ? "px-5 py-4 text-xs font-semibold text-positive" : "px-5 py-4 text-xs font-semibold text-negative"}>{trade.side}</td>
                <td className="px-5 py-4 font-mono">{trade.quantity}</td>
                <td className="px-5 py-4 font-mono">{trade.price}</td>
                <td className="px-5 py-4 text-right text-xs text-slate-500">{trade.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

