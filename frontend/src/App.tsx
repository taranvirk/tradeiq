import { lazy, Suspense, type ReactNode } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/AuthState";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { useHealth } from "./hooks/useHealth";

const Dashboard = lazy(() => import("./pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const Markets = lazy(() => import("./pages/Markets"));
const Signals = lazy(() => import("./pages/Signals"));
const Backtests = lazy(() => import("./pages/Backtests"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const RiskCenter = lazy(() => import("./pages/RiskCenter"));
const Landing = lazy(() => import("./pages/Landing"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const ProfileSettings = lazy(() => import("./pages/ProfileSettings"));
const TradingSettings = lazy(() => import("./pages/TradingSettings"));
const PaperPortfolioSettings = lazy(() => import("./pages/PaperPortfolioSettings"));

function LoadingAccount() { return <div className="grid min-h-screen place-items-center bg-canvas"><div className="text-center"><div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-slate-700 border-t-accent" /><p className="mt-4 text-sm text-slate-500">Loading account…</p></div></div>; }

function PublicOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingAccount />;
  if (user) return <Navigate to={user.onboarding_required ? "/onboarding" : "/dashboard"} replace />;
  return children;
}

function ProtectedRoute() {
  const { user, loading } = useAuth(); const location = useLocation();
  if (loading) return <LoadingAccount />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user.onboarding_required) return <Navigate to="/onboarding" replace />;
  return <Outlet />;
}

function OnboardingRoute() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingAccount />;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.onboarding_required) return <Navigate to="/dashboard" replace />;
  return <Onboarding />;
}

function AppShell() {
  const { data: health, isError } = useHealth();
  return <div className="min-h-screen bg-canvas text-slate-300"><div className="flex min-h-screen"><Sidebar /><div className="min-w-0 flex-1 pb-20 lg:pb-0"><Topbar health={health} isError={isError} /><Suspense fallback={<main className="page-shell"><div className="panel-card h-80 animate-pulse" /></main>}><Outlet /></Suspense></div></div></div>;
}

function ApplicationRoutes() {
  return <Suspense fallback={<LoadingAccount />}><Routes>
    <Route path="/" element={<PublicOnly><Landing /></PublicOnly>} />
    <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
    <Route path="/signup" element={<PublicOnly><Signup /></PublicOnly>} />
    <Route path="/onboarding" element={<OnboardingRoute />} />
    <Route element={<ProtectedRoute />}><Route element={<AppShell />}>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/stocks" element={<Markets />} />
      <Route path="/watchlist" element={<Navigate to="/stocks" replace />} />
      <Route path="/ai" element={<Signals />} />
      <Route path="/backtests" element={<Backtests />} />
      <Route path="/portfolio" element={<Portfolio />} />
      <Route path="/trades" element={<Navigate to="/portfolio" replace />} />
      <Route path="/risk" element={<RiskCenter />} />
      <Route path="/settings/profile" element={<ProfileSettings />} />
      <Route path="/settings/trading" element={<TradingSettings />} />
      <Route path="/settings/portfolio" element={<PaperPortfolioSettings />} />
    </Route></Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Suspense>;
}

export default function App() { return <BrowserRouter><AuthProvider><ApplicationRoutes /></AuthProvider></BrowserRouter>; }
