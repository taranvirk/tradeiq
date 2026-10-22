import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const equityData = [
  { month: "Oct", value: 10000 },
  { month: "Nov", value: 10180 },
  { month: "Dec", value: 10060 },
  { month: "Jan", value: 10490 },
  { month: "Feb", value: 10780 },
  { month: "Mar", value: 10640 },
  { month: "Apr", value: 11120 },
  { month: "May", value: 11540 },
  { month: "Jun", value: 11420 },
  { month: "Jul", value: 11960 },
  { month: "Aug", value: 12180 },
  { month: "Sep", value: 12543 },
];

function currency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function PortfolioChart() {
  return (
    <section className="panel-card min-h-[370px] p-5 sm:p-6">
      <div className="mb-7 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-eyebrow">Portfolio performance</p>
          <div className="mt-2 flex items-baseline gap-3">
            <h2 className="font-mono text-2xl font-semibold text-white">$12,543.18</h2>
            <span className="text-sm font-medium text-positive">+25.43%</span>
          </div>
        </div>
        <div className="flex rounded-lg border border-line bg-[#090f1b] p-1 text-xs">
          {['1M', '3M', 'YTD', '1Y'].map((period) => (
            <span key={period} className={period === '1Y' ? "rounded-md bg-slate-800 px-2.5 py-1.5 text-white" : "px-2.5 py-1.5 text-slate-600"}>
              {period}
            </span>
          ))}
        </div>
      </div>

      <div className="h-[265px] w-full" aria-label="Demo portfolio equity chart">
        <ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 800, height: 265 }}>
          <AreaChart data={equityData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#5eead4" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#5eead4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1b2739" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="month" stroke="#536176" tickLine={false} axisLine={false} fontSize={11} />
            <YAxis stroke="#536176" tickLine={false} axisLine={false} fontSize={11} tickFormatter={currency} width={64} />
            <Tooltip
              formatter={(value) => [currency(Number(value ?? 0)), "Equity"]}
              contentStyle={{ background: "#0d1422", border: "1px solid #26354a", borderRadius: 10, fontSize: 12 }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Area type="monotone" dataKey="value" stroke="#5eead4" strokeWidth={2} fill="url(#equityFill)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
