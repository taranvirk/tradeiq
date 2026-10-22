import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthState";
import { apiMessage } from "../services/api";
import { AuthPage, Field } from "./Login";

export default function Signup() {
  const { signUp } = useAuth(); const navigate = useNavigate();
  const [fields, setFields] = useState({ first_name: "", last_name: "", email: "", password: "", confirm_password: "" });
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const set = (key: keyof typeof fields) => (value: string) => setFields((current) => ({ ...current, [key]: value }));
  const submit = async (event: FormEvent) => { event.preventDefault(); setError(""); if (fields.password !== fields.confirm_password) { setError("Passwords do not match."); return; } if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}/.test(fields.password)) { setError("Use at least 8 characters with uppercase, lowercase, and a number."); return; } setLoading(true); try { await signUp(fields); navigate("/onboarding"); } catch (cause) { setError(apiMessage(cause)); } finally { setLoading(false); } };
  return <AuthPage title="Create your TradeIQ account" subtitle="Start with simulated funds—no real deposit required."><form onSubmit={submit} className="space-y-4"><div className="grid grid-cols-2 gap-3"><Field label="First name" value={fields.first_name} onChange={set("first_name")} autoComplete="given-name" /><Field label="Last name" value={fields.last_name} onChange={set("last_name")} autoComplete="family-name" /></div><Field label="Email" type="email" value={fields.email} onChange={set("email")} autoComplete="email" /><Field label="Password" type="password" value={fields.password} onChange={set("password")} autoComplete="new-password" /><Field label="Confirm password" type="password" value={fields.confirm_password} onChange={set("confirm_password")} autoComplete="new-password" /><p className="text-xs leading-5 text-slate-600">Minimum 8 characters with uppercase, lowercase, and a number.</p>{error && <p role="alert" className="rounded-lg border border-negative/20 bg-negative/10 p-3 text-sm text-negative">{error}</p>}<button disabled={loading} className="primary-button w-full">{loading ? "Creating account…" : "Create account"}</button></form><p className="mt-6 text-center text-sm text-slate-500">Already have an account? <Link className="font-medium text-accent" to="/login">Sign in</Link></p></AuthPage>;
}
