import type { components } from "./schema";

export type Meta = components["schemas"]["MetaResponse"];
export type User = components["schemas"]["UserOut"];
export type LoginResponse = components["schemas"]["LoginResponse"];
export type Faculty = components["schemas"]["FacultyOut"];
export type DashboardSummary = components["schemas"]["DashboardSummaryOut"];
export type DashboardTrend = components["schemas"]["DashboardTrendOut"];
export type RiskByFaculty = components["schemas"]["RiskByFacultyOut"];
export type FacultyRisk = components["schemas"]["FacultyRiskOut"];
export type TrendWeek = components["schemas"]["TrendWeekOut"];

const TOKEN_KEY = "edupredict.token";
const USER_KEY = "edupredict.user";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as User;
    if (
      typeof parsed.id !== "number" ||
      typeof parsed.name !== "string" ||
      typeof parsed.role !== "string"
    ) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveSession(token: string, user: User): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authenticated) {
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...init, headers });
  } catch {
    throw new Error("No se pudo conectar con la API");
  }

  if (!response.ok) {
    let message = "Ocurrió un error inesperado";
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export const api = {
  meta: () => request<Meta>("/meta", {}, false),
  login: (email: string, password: string) =>
    request<LoginResponse>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ email, password }),
      },
      false,
    ),
  me: () => request<User>("/auth/me"),
  faculties: () => request<Faculty[]>("/faculties"),
  dashboardSummary: (facultyId?: number) =>
    request<DashboardSummary>(
      facultyId
        ? `/dashboard/summary?faculty_id=${facultyId}`
        : "/dashboard/summary",
    ),
  dashboardTrend: () => request<DashboardTrend>("/dashboard/trend"),
  riskByFaculty: () =>
    request<RiskByFaculty>("/dashboard/risk-by-faculty"),
};
