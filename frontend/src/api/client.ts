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
export type TutorSummary = components["schemas"]["TutorSummaryOut"];
export type StudentListItem = components["schemas"]["StudentListItemOut"];
export type StudentDetail = components["schemas"]["StudentDetailOut"];
export type Intervention = components["schemas"]["InterventionOut"];
export type InterventionCreate = components["schemas"]["InterventionCreate"];
export type TopFactor = components["schemas"]["TopFactorOut"];
export type ModelInfo = components["schemas"]["ModelInfoOut"];
export type FeatureImportance = components["schemas"]["FeatureImportanceOut"];
export type ModelMetrics = components["schemas"]["ModelMetricsOut"];
export type UploadResult = components["schemas"]["UploadResultOut"];
export type PipelineStep = components["schemas"]["PipelineStepOut"];
export type PipelineError = components["schemas"]["PipelineErrorOut"];
export type RiskDistribution = components["schemas"]["RiskDistributionOut"];
export type ModelViewRow = components["schemas"]["ModelViewRowOut"];
export type RiskLevel = StudentListItem["risk_level"];
export type InterventionType = Intervention["type"];

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

async function errorFromResponse(response: Response): Promise<ApiError> {
  let message = "Ocurrió un error inesperado";
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      message = body.detail;
    }
  } catch {
    message = response.statusText || message;
  }
  return new ApiError(response.status, message);
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  authenticated = true,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (typeof init.body === "string" && !headers.has("Content-Type")) {
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
    throw await errorFromResponse(response);
  }

  return (await response.json()) as T;
}

async function requestBlob(path: string): Promise<Blob> {
  const headers = new Headers();
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`/api${path}`, { headers });
  } catch {
    throw new Error("No se pudo conectar con la API");
  }

  if (!response.ok) {
    throw await errorFromResponse(response);
  }

  return response.blob();
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
  tutorSummary: () => request<TutorSummary>("/tutor/summary"),
  students: (params: { risk?: RiskLevel; q?: string } = {}) => {
    const search = new URLSearchParams();
    if (params.risk) {
      search.set("risk", params.risk);
    }
    if (params.q?.trim()) {
      search.set("q", params.q.trim());
    }
    const query = search.toString();
    return request<StudentListItem[]>(
      `/students${query ? `?${query}` : ""}`,
    );
  },
  studentDetail: (id: number) =>
    request<StudentDetail>(`/students/${id}`),
  createIntervention: (id: number, payload: InterventionCreate) =>
    request<Intervention>(`/students/${id}/interventions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  modelInfo: () => request<ModelInfo>("/model/info"),
  uploadTemplate: () => requestBlob("/upload/template.csv"),
  uploadCsv: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<UploadResult>("/upload", { method: "POST", body });
  },
};
