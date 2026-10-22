import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState } from "react";

import { apiMessage, getStocks } from "../services/api";

const exchanges = [
  { value: "", label: "All" },
  { value: "NASDAQ", label: "NASDAQ" },
  { value: "NYSE", label: "NYSE" },
  { value: "TSX", label: "TSX" },
  { value: "TSXV", label: "TSXV" },
];

interface StockPickerProps {
  value: string;
  onChange: (symbol: string) => void;
  label?: string;
}

export function StockPicker({ value, onChange, label = "Choose a stock" }: StockPickerProps) {
  const [search, setSearch] = useState("");
  const [exchange, setExchange] = useState("");
  const stocks = useQuery({
    queryKey: ["stock-picker", search, exchange],
    queryFn: () => getStocks(search, exchange),
  });

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <label htmlFor={`stock-search-${label.replaceAll(" ", "-")}`} className="text-xs font-medium text-slate-400">{label}</label>
        <span className="font-mono text-xs text-accent">{value}</span>
      </div>
      <div className="relative mt-2">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" size={15} />
        <input
          id={`stock-search-${label.replaceAll(" ", "-")}`}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search ticker or company"
          className="control w-full pl-9"
        />
      </div>
      <div className="mt-2 flex flex-wrap gap-1" aria-label="Filter by exchange">
        {exchanges.map((item) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setExchange(item.value)}
            className={`rounded-md px-2.5 py-1 text-[10px] font-semibold tracking-wide ${exchange === item.value ? "bg-accent text-slate-950" : "bg-canvas/70 text-slate-500 hover:text-white"}`}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div role="listbox" aria-label="Available stocks" className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-line bg-canvas/50 p-1">
        {stocks.isLoading ? <p className="p-3 text-xs text-slate-600">Loading stocks…</p> : stocks.isError ? <p className="p-3 text-xs text-negative">{apiMessage(stocks.error)}</p> : !stocks.data?.length ? <p className="p-3 text-xs text-slate-600">No matching stocks.</p> : stocks.data.map((stock) => (
          <button
            key={stock.symbol}
            type="button"
            role="option"
            aria-selected={stock.symbol === value}
            onClick={() => onChange(stock.symbol)}
            className={`flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left ${stock.symbol === value ? "bg-accent/10 text-white" : "text-slate-400 hover:bg-slate-800/60 hover:text-white"}`}
          >
            <span className="min-w-0">
              <strong className="font-mono text-xs">{stock.symbol}</strong>
              <span className="ml-2 truncate text-[10px] text-slate-600">{stock.company_name}</span>
            </span>
            <span className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-[9px] text-slate-500">{stock.exchange}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

