import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  api,
  ApiError,
  clearSession,
  getStoredUser,
  getToken,
  saveSession,
  type User,
} from "@/api/client";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function homePathForRole(role: string): string {
  return role === "director" ? "/dashboard" : "/students";
}

export function roleLabel(role: string): string {
  if (role === "director") {
    return "Directivo";
  }
  if (role === "tutor") {
    return "Tutor";
  }
  return role;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<User | null>(() =>
    getToken() ? getStoredUser() : null,
  );

  const meQuery = useQuery({
    queryKey: ["auth", "me"],
    queryFn: api.me,
    enabled: Boolean(token),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (meQuery.data && token) {
      setUser(meQuery.data);
      saveSession(token, meQuery.data);
    }
  }, [meQuery.data, token]);

  useEffect(() => {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      clearSession();
      setToken(null);
      setUser(null);
      queryClient.removeQueries({ queryKey: ["auth", "me"] });
    }
  }, [meQuery.error, queryClient]);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login(email, password);
      saveSession(response.access_token, response.user);
      setToken(response.access_token);
      setUser(response.user);
      queryClient.setQueryData(["auth", "me"], response.user);
      return response.user;
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  const isLoading = Boolean(token) && meQuery.isPending;

  const value = useMemo(
    () => ({ user, isLoading, login, logout }),
    [user, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
