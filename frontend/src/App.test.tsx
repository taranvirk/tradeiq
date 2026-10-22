import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("./hooks/useHealth", () => ({
  useHealth: () => ({ data: { status: "healthy", database: "connected", redis: "connected", market_api: "demo", version: "0.1.0" }, isError: false }),
}));

vi.mock("./pages/Dashboard", () => ({
  Dashboard: () => <h1>Portfolio command center</h1>,
}));

vi.mock("./services/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("./services/api")>();
  return {
    ...original,
    getMe: vi.fn().mockResolvedValue({ id: 1, first_name: "TradeIQ", last_name: "Demo", full_name: "TradeIQ Demo", email: "demo@tradeiq.dev", is_demo: true, created_at: "2026-01-01T00:00:00Z", onboarding_required: false }),
  };
});

function renderApp() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}><App /></QueryClientProvider>);
}

describe("App authentication routing", () => {
  beforeEach(() => { localStorage.clear(); window.history.pushState({}, "", "/"); });

  it("shows the public landing page to a visitor", async () => {
    renderApp();
    expect(await screen.findByRole("heading", { name: /ai-powered market analysis/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /create free account/i })).toHaveAttribute("href", "/signup");
  });

  it("restores a valid session before rendering a protected dashboard", async () => {
    localStorage.setItem("tradeiq-token", "valid-test-token");
    window.history.pushState({}, "", "/dashboard");
    renderApp();
    expect(screen.getByText(/loading account/i)).toBeInTheDocument();
    expect(await screen.findByText("Systems online", {}, { timeout: 10_000 })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Overview" })).toHaveLength(2);
  });
});
