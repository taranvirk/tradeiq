import axios, { type AxiosRequestConfig } from "axios";

import type { Analytics, AuthResponse, Backtest, DashboardData, HealthResponse, ModelInfo, Order, PaperAccount, Portfolio, Prediction, RiskData, Stock, StockHistory, Trade, User } from "../types/api";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000",
  timeout: 15_000,
  headers: { Accept: "application/json" },
});

export const TOKEN_KEY = "tradeiq-token";

async function authed<T>(config: AxiosRequestConfig): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) throw new Error("Authentication required");
  try {
    const response = await api.request<T>({ ...config, headers: { ...config.headers, Authorization: `Bearer ${token}` } });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event("tradeiq-auth-expired"));
    }
    throw error;
  }
}

export const getHealth = async (): Promise<HealthResponse> => (await api.get<HealthResponse>("/health")).data;
export const register = async (data: { first_name: string; last_name: string; email: string; password: string; confirm_password: string }): Promise<AuthResponse> => (await api.post<AuthResponse>("/api/v1/auth/register", data)).data;
export const login = async (email: string, password: string): Promise<AuthResponse> => (await api.post<AuthResponse>("/api/v1/auth/login", { email, password })).data;
export const demoLogin = async (): Promise<AuthResponse> => (await api.post<AuthResponse>("/api/v1/auth/demo")).data;
export const logout = (): Promise<void> => authed({ method: "POST", url: "/api/v1/auth/logout" });
export const getMe = (): Promise<User> => authed({ url: "/api/v1/auth/me" });
export const createPaperAccount = (starting_balance: number): Promise<PaperAccount> => authed({ method: "POST", url: "/api/v1/paper-account", data: { starting_balance } });
export const getPaperAccount = (): Promise<PaperAccount> => authed({ url: "/api/v1/paper-account" });
export const resetPaperAccount = (starting_balance: number, confirmation: string): Promise<PaperAccount> => authed({ method: "POST", url: "/api/v1/paper-account/reset", data: { starting_balance, confirmation } });
export const getProfile = (): Promise<{ first_name: string; last_name: string; email: string; created_at: string }> => authed({ url: "/api/v1/settings/profile" });
export const updateProfile = (data: { first_name: string; last_name: string }): Promise<{ first_name: string; last_name: string; email: string; created_at: string }> => authed({ method: "PATCH", url: "/api/v1/settings/profile", data });
export const getTradingSettings = (): Promise<PaperAccount> => authed({ url: "/api/v1/settings/trading" });
export const updateTradingSettings = (data: Record<string, unknown>): Promise<PaperAccount> => authed({ method: "PATCH", url: "/api/v1/settings/trading", data });
export const getDashboard = (): Promise<DashboardData> => authed({ url: "/api/v1/dashboard" });
export const getStocks = (q = "", exchange = ""): Promise<Stock[]> => authed({ url: "/api/v1/stocks", params: { q, exchange: exchange || undefined, limit: 100 } });
export const getStock = (symbol: string): Promise<Stock> => authed({ url: `/api/v1/stocks/${symbol}` });
export const getHistory = (symbol: string, range: string): Promise<StockHistory> => authed({ url: `/api/v1/stocks/${symbol}/history`, params: { range } });
export const getWatchlist = (): Promise<Stock[]> => authed({ url: "/api/v1/watchlist" });
export const addWatchlist = (symbol: string): Promise<{ added: boolean }> => authed({ method: "POST", url: `/api/v1/watchlist/${symbol}` });
export const removeWatchlist = (symbol: string): Promise<void> => authed({ method: "DELETE", url: `/api/v1/watchlist/${symbol}` });
export const getPredictions = (): Promise<Prediction[]> => authed({ url: "/api/v1/scanner" });
export const getModels = (): Promise<ModelInfo[]> => authed({ url: "/api/v1/models" });
export const trainModel = (symbol: string): Promise<{ prediction: Prediction }> => authed({ method: "POST", url: `/api/v1/models/train/${symbol}`, timeout: 120_000 });
export const getBacktests = (): Promise<Backtest[]> => authed({ url: "/api/v1/backtests" });
export const getBacktest = (id: number): Promise<Backtest> => authed({ url: `/api/v1/backtests/${id}` });
export const createBacktest = (data: Record<string, unknown>): Promise<Backtest> => authed({ method: "POST", url: "/api/v1/backtests", data, timeout: 60_000 });
export const getPortfolio = (): Promise<Portfolio> => authed({ url: "/api/v1/portfolio" });
export const getTrades = (): Promise<Trade[]> => authed({ url: "/api/v1/trades" });
export const getAnalytics = (): Promise<Analytics> => authed({ url: "/api/v1/analytics" });
export const getRisk = (): Promise<RiskData> => authed({ url: "/api/v1/risk" });
export const calculatePositionSize = (data: Record<string, unknown>): Promise<{ quantity: number; position_value: number }> => authed({ method: "POST", url: "/api/v1/risk/position-size", data });
export const submitOrder = (data: Record<string, unknown>): Promise<Order> => authed({ method: "POST", url: "/api/v1/orders", data });

export function apiMessage(error: unknown): string {
  if (axios.isAxiosError<{ message?: string; detail?: string }>(error)) return error.response?.data?.message ?? error.response?.data?.detail ?? error.message;
  return "Something went wrong. Please try again.";
}

export { api };
