import { AlertTriangle, Inbox } from "lucide-react";

export function LoadingPanel({ label = "Loading market intelligence" }: { label?: string }) {
  return <div className="panel-card grid min-h-48 place-items-center p-8 text-sm text-slate-500"><span className="animate-pulse">{label}…</span></div>;
}

export function ErrorPanel({ message }: { message: string }) {
  return <div className="panel-card flex min-h-48 flex-col items-center justify-center gap-3 p-8 text-center"><AlertTriangle className="text-negative" /><p className="text-sm text-slate-300">{message}</p><p className="text-xs text-slate-600">Verify the API is online and try again.</p></div>;
}

export function EmptyPanel({ message }: { message: string }) {
  return <div className="panel-card flex min-h-40 flex-col items-center justify-center gap-3 p-8 text-center"><Inbox className="text-slate-600" /><p className="text-sm text-slate-500">{message}</p></div>;
}
