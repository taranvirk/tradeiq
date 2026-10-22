import { createContext, useContext } from "react";

import type { User } from "../types/api";

export interface SignupFields { first_name: string; last_name: string; email: string; password: string; confirm_password: string }
export interface AuthValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signUp: (fields: SignupFields) => Promise<User>;
  viewDemo: () => Promise<User>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<User | null>;
}

export const AuthState = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const value = useContext(AuthState);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
