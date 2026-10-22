import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { demoLogin, getMe, login as loginRequest, logout as logoutRequest, register, TOKEN_KEY } from "../services/api";
import type { User } from "../types/api";
import { AuthState, type AuthValue } from "./AuthState";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)));

  const refreshUser = useCallback(async () => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const current = await getMe();
      setUser(current);
      return current;
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (localStorage.getItem(TOKEN_KEY)) {
      void getMe().then(setUser).catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
      }).finally(() => setLoading(false));
    }
    const expired = () => setUser(null);
    window.addEventListener("tradeiq-auth-expired", expired);
    return () => window.removeEventListener("tradeiq-auth-expired", expired);
  }, []);

  const accept = (accessToken: string, nextUser: User) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setUser(nextUser);
    return nextUser;
  };

  const value = useMemo<AuthValue>(() => ({
    user,
    loading,
    signIn: async (email, password) => { const response = await loginRequest(email, password); return accept(response.access_token, response.user); },
    signUp: async (fields) => { const response = await register(fields); return accept(response.access_token, response.user); },
    viewDemo: async () => { const response = await demoLogin(); return accept(response.access_token, response.user); },
    signOut: async () => {
      try { if (localStorage.getItem(TOKEN_KEY)) await logoutRequest(); } finally { localStorage.removeItem(TOKEN_KEY); setUser(null); }
    },
    refreshUser,
  }), [loading, refreshUser, user]);

  return <AuthState.Provider value={value}>{children}</AuthState.Provider>;
}
