import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { EmptyPanel, ErrorPanel, LoadingPanel } from "../components/QueryState";
import { StockPicker } from "../components/StockPicker";
import { apiMessage, getModels, getPredictions, trainModel } from "../services/api";
import type { Prediction } from "../types/api";

function factorLabel(factor: string | { feature: string; impact: number; value: number }) {
  return typeof factor === "string" ? factor : `${factor.feature.replaceAll("_", " ")} (${factor.value})`;
}

export default function Signals() {
  const [selected, setSelected] = useState("NVDA");
  const [minimum, setMinimum] = useState(0);
  const client = useQueryClient();
  const predictions = useQuery({ queryKey: ["predictions"], queryFn: getPredictions });
  const models = useQuery({ queryKey: ["models"], queryFn: getModels });
  const train = useMutation({
    mutationFn: () => trainModel(selected),
    onSuccess: ({ prediction }) => {
      client.setQueryData<Prediction[]>(["predictions"], (current = []) => [
        prediction,
        ...current.filter((item) => item.symbol !== prediction.symbol),
      ]);
      void client.invalidateQueries({ queryKey: ["models"] });
    },
  });
  const filtered = useMemo(
    () => predictions.data?.filter((item) => item.probability_up * 100 >= minimum) ?? [],
    [predictions.data, minimum],
  );
  const detail = predictions.data?.find((item) => item.symbol === selected);

  if (predictions.isLoading || models.isLoading) return <main className="page-shell"><LoadingPanel label="Scoring the market" /></main>;
  if (predictions.isError || models.isError) return <main className="page-shell"><ErrorPanel message={apiMessage(predictions.error ?? models.error)} /></main>;

  return (
    <main className="page-shell">
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div><span className="demo-badge">Explainable AI</span><h1 className="page-title mt-3">Opportunity scanner</h1><p className="mt-2 text-sm text-slate-500">Choose any supported US or Canadian stock and generate an explainable directional signal.</p></div>
        <button className="primary-button" disabled={train.isPending} onClick={() => train.mutate()}>{train.isPending ? `Training ${selected} chronologically…` : `${detail ? "Retrain" : "Generate signal for"} ${selected}`}</button>
      </div>

      <section className="panel-card mb-4 grid gap-5 p-5 xl:grid-cols-[minmax(320px,.8fr)_minmax(0,1.2fr)]">
        <StockPicker value={selected} onChange={(symbol) => { setSelected(symbol); train.reset(); }} label="Stock to analyze" />
        {detail ? <SignalDetail detail={detail} /> : <div className="grid min-h-48 place-items-center rounded-xl border border-dashed border-line bg-canvas/30 p-6 text-center"><div><Sparkles className="mx-auto text-slate-700" size={24} /><p className="mt-3 text-sm font-medium text-white">No saved signal for {selected}</p><p className="mt-1 text-xs text-slate-600">Generate a signal to train the models on this stock’s chronological history.</p></div></div>}
      </section>
      {train.isError && <p className="mb-4 rounded-lg border border-negative/20 bg-negative/10 p-3 text-sm text-negative">{apiMessage(train.error)}</p>}

      <div className="mb-4 panel-card flex flex-wrap items-center gap-4 p-4"><label className="text-xs text-slate-500" htmlFor="confidence">Minimum probability up</label><input id="confidence" type="range" min="0" max="90" step="5" value={minimum} onChange={(event) => setMinimum(Number(event.target.value))} className="accent-teal-300" /><span className="font-mono text-sm text-accent">{minimum}%</span><span className="ml-auto text-xs text-slate-600">{filtered.length} saved opportunities</span></div>
      {!filtered.length ? <EmptyPanel message="No saved signals match this confidence filter. Choose a stock above to generate one." /> : <section className="panel-card overflow-hidden"><div className="grid grid-cols-[1fr_1fr_1fr] border-b border-line bg-canvas/40 px-5 py-3 text-[10px] uppercase tracking-wider text-slate-600"><span>Symbol</span><span>Signal</span><span className="text-right">Probability up</span></div>{filtered.map((item, index) => <button key={item.symbol} onClick={() => setSelected(item.symbol)} className={`grid w-full grid-cols-[1fr_1fr_1fr] items-center border-b border-line/60 px-5 py-4 text-left transition last:border-0 ${selected === item.symbol ? "bg-accent/5" : "hover:bg-slate-800/30"}`}><span><strong className="font-mono text-white">{item.symbol}</strong><small className="ml-3 text-slate-700">#{index + 1}</small></span><span><span className={item.prediction === "BUY" ? "signal-buy" : item.prediction === "SELL" ? "signal-sell" : "signal-hold"}>{item.prediction}</span></span><span className="text-right"><strong className="font-mono text-white">{(item.probability_up * 100).toFixed(1)}%</strong><span className="ml-2 text-[10px] text-slate-600">{(item.confidence * 100).toFixed(0)}% conf.</span></span></button>)}</section>}

      <section className="panel-card mt-4 overflow-hidden"><div className="flex items-center gap-3 p-5"><BrainCircuit className="text-accent" size={19} /><div><p className="section-eyebrow">Model registry</p><h2 className="mt-1 font-semibold text-white">Versioned experiments</h2></div></div><div className="overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead className="border-y border-line bg-canvas/40 text-[10px] uppercase tracking-wider text-slate-600"><tr><th className="px-5 py-3">Version</th><th>Algorithm</th><th>Accuracy</th><th>F1</th><th>ROC-AUC</th><th>Status</th></tr></thead><tbody>{models.data?.map((model) => <tr key={model.id} className="border-b border-line/60 last:border-0"><td className="max-w-64 truncate px-5 py-4 font-mono text-xs text-slate-300">{model.version}</td><td>{model.algorithm.replaceAll("_", " ")}</td><td>{typeof model.metrics.accuracy === "number" ? (model.metrics.accuracy * 100).toFixed(1) + "%" : "—"}</td><td>{typeof model.metrics.f1 === "number" ? model.metrics.f1.toFixed(3) : "—"}</td><td>{typeof model.metrics.roc_auc === "number" ? model.metrics.roc_auc.toFixed(3) : "—"}</td><td><span className={model.is_active ? "signal-buy" : "signal-hold"}>{model.is_active ? "ACTIVE" : "ARCHIVED"}</span></td></tr>)}</tbody></table></div></section>
    </main>
  );
}

function SignalDetail({ detail }: { detail: Prediction }) {
  return <div><div className="flex items-start justify-between"><div><p className="section-eyebrow">Decision explanation</p><h2 className="mt-2 font-mono text-xl font-semibold text-white">{detail.symbol} · {detail.prediction}</h2></div><div className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent"><Sparkles size={19} /></div></div><div className="mt-4 rounded-xl border border-accent/10 bg-accent/5 p-4"><p className="text-xs text-slate-500">Probability of positive next-period return</p><p className="mt-2 font-mono text-3xl text-accent">{(detail.probability_up * 100).toFixed(1)}%</p></div><div className="mt-4 grid gap-4 md:grid-cols-2"><div><p className="text-[10px] font-semibold uppercase tracking-wider text-positive">Positive factors</p><ul className="mt-2 space-y-2">{detail.explanation.positive_factors.map((factor, index) => <li key={index} className="rounded-lg bg-positive/5 px-3 py-2 text-xs text-slate-300">+ {factorLabel(factor)}</li>)}</ul></div><div><p className="text-[10px] font-semibold uppercase tracking-wider text-negative">Risk factors</p><ul className="mt-2 space-y-2">{detail.explanation.negative_factors.length ? detail.explanation.negative_factors.map((factor, index) => <li key={index} className="rounded-lg bg-negative/5 px-3 py-2 text-xs text-slate-300">− {factorLabel(factor)}</li>) : <li className="text-xs text-slate-600">No dominant negative factor.</li>}</ul></div></div><p className="mt-4 break-all text-[10px] text-slate-700">Model: {detail.model_version}</p></div>;
}
