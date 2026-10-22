import type { Candle } from "../types/api";

export function CandlestickChart({ data }: { data: Candle[] }) {
  const candles = data.slice(-90);
  if (!candles.length) return null;
  const width = 900, height = 270, pad = 18;
  const high = Math.max(...candles.map((item) => item.high));
  const low = Math.min(...candles.map((item) => item.low));
  const scaleY = (value: number) => pad + (high - value) / Math.max(high - low, 0.01) * (height - pad * 2);
  const step = (width - pad * 2) / candles.length;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Candlestick price chart" className="h-full w-full overflow-visible">
      {[0.25, 0.5, 0.75].map((point) => <line key={point} x1={pad} x2={width - pad} y1={height * point} y2={height * point} stroke="#1b2739" />)}
      {candles.map((item, index) => {
        const rising = item.close >= item.open;
        const color = rising ? "#4ade80" : "#fb7185";
        const x = pad + index * step + step / 2;
        const bodyTop = scaleY(Math.max(item.open, item.close));
        const bodyHeight = Math.max(1.5, Math.abs(scaleY(item.open) - scaleY(item.close)));
        return <g key={item.timestamp}><line x1={x} x2={x} y1={scaleY(item.high)} y2={scaleY(item.low)} stroke={color} strokeWidth={1} /><rect x={x - Math.max(1.2, step * 0.28)} y={bodyTop} width={Math.max(2.4, step * 0.56)} height={bodyHeight} fill={rising ? "#4ade80" : "#fb7185"} opacity={0.85}><title>{`${new Date(item.timestamp).toLocaleDateString()} O ${item.open.toFixed(2)} H ${item.high.toFixed(2)} L ${item.low.toFixed(2)} C ${item.close.toFixed(2)}`}</title></rect></g>;
      })}
    </svg>
  );
}
