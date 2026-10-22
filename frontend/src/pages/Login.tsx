import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthState";
import { Brand } from "../components/Brand";
import { apiMessage } from "../services/api";

export default function Login() {
  const { signIn, viewDemo } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setLoading(true); setError(""); try { const user = await signIn(email, password); navigate(user.onboarding_required ? "/onboarding" : "/dashboard"); } catch (cause) { setError(apiMessage(cause)); } finally { setLoading(false); } };
  const demo = async () => { setLoading(true); setError(""); try { await viewDemo(); navigate("/dashboard"); } catch (cause) { setError(apiMessage(cause)); } finally { setLoading(false); } };
  return <AuthPage title="Welcome back" subtitle="Sign in to your TradeIQ account."><form onSubmit={submit} className="space-y-4"><Field label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" /><Field label="Password" type="password" value={password} onChange={setPassword} autoComplete="current-password" />{error && <p role="alert" className="rounded-lg border border-negative/20 bg-negative/10 p-3 text-sm text-negative">{error}</p>}<button disabled={loading} className="primary-button w-full">{loading ? "Signing in…" : "Sign in"}</button><button type="button" disabled={loading} onClick={demo} className="w-full rounded-lg border border-line px-4 py-2.5 text-sm font-semibold text-white hover:border-accent/40">View demo account</button></form><p className="mt-6 text-center text-sm text-slate-500">Don't have an account? <Link className="font-medium text-accent" to="/signup">Create account</Link></p></AuthPage>;
}

export function AuthPage({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) { return <div className="grid min-h-screen place-items-center bg-canvas px-4 py-10"><div className="w-full max-w-md"><Link to="/" className="mb-8 flex justify-center"><Brand /></Link><section className="panel-card p-6 sm:p-8"><h1 className="text-2xl font-semibold text-white">{title}</h1><p className="mb-7 mt-2 text-sm text-slate-500">{subtitle}</p>{children}</section></div></div>; }

export function Field({ label, type = "text", value, onChange, autoComplete }: { label: string; type?: string; value: string; onChange: (value: string) => void; autoComplete?: string }) { return <label className="block text-sm text-slate-400">{label}<input required type={type} value={value} onChange={(event) => onChange(event.target.value)} autoComplete={autoComplete} className="control mt-2 w-full" /></label>; }
