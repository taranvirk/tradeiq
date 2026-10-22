import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../auth/AuthState";
import { ErrorPanel, LoadingPanel } from "../components/QueryState";
import { apiMessage, getProfile, updateProfile } from "../services/api";

type Profile = { first_name: string; last_name: string; email: string; created_at: string };

export default function ProfileSettings() {
  const query = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  if (query.isLoading) return <main className="page-shell"><LoadingPanel label="Loading profile" /></main>;
  if (query.isError || !query.data) return <main className="page-shell"><ErrorPanel message={apiMessage(query.error)} /></main>;
  return <ProfileForm key={`${query.data.first_name}-${query.data.last_name}`} profile={query.data} />;
}

function ProfileForm({ profile }: { profile: Profile }) {
  const client = useQueryClient(); const { refreshUser } = useAuth();
  const [firstName, setFirstName] = useState(profile.first_name); const [lastName, setLastName] = useState(profile.last_name); const [saved, setSaved] = useState(false);
  const mutation = useMutation({ mutationFn: () => updateProfile({ first_name: firstName, last_name: lastName }), onSuccess: async () => { setSaved(true); await refreshUser(); await client.invalidateQueries({ queryKey: ["profile"] }); } });
  const submit = (event: FormEvent) => { event.preventDefault(); setSaved(false); mutation.mutate(); };
  return <main className="page-shell"><div className="mb-7"><p className="section-eyebrow">Account settings</p><h1 className="page-title mt-2">Profile</h1><p className="mt-2 text-sm text-slate-500">Manage the name shown throughout your TradeIQ account.</p></div><form onSubmit={submit} className="panel-card max-w-2xl p-6"><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm text-slate-400">First name<input className="control mt-2 w-full" value={firstName} onChange={(event) => setFirstName(event.target.value)} required /></label><label className="text-sm text-slate-400">Last name<input className="control mt-2 w-full" value={lastName} onChange={(event) => setLastName(event.target.value)} required /></label></div><label className="mt-4 block text-sm text-slate-400">Email<input className="control mt-2 w-full opacity-70" value={profile.email} disabled /></label><div className="mt-4 rounded-lg border border-line bg-canvas/50 p-4 text-sm"><span className="text-slate-500">Account created</span><span className="float-right text-slate-300">{new Date(profile.created_at).toLocaleDateString()}</span></div>{mutation.isError && <p className="mt-4 text-sm text-negative">{apiMessage(mutation.error)}</p>}{saved && <p className="mt-4 text-sm text-positive">Profile updated.</p>}<button className="primary-button mt-5" disabled={mutation.isPending}>Save profile</button></form></main>;
}
