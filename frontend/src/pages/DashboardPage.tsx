import { useState, type ReactNode } from "react";
import {
  AlertTriangle,
  BellRing,
  CalendarDays,
  ChevronDown,
  CircleAlert,
  Loader2,
  Percent,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "@/api/client";
import { useMeta } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type KpiTone = "indigo" | "emerald" | "red" | "amber";

const toneStyles: Record<KpiTone, string> = {
  indigo: "bg-indigo-50 text-indigo-600",
  emerald: "bg-emerald-50 text-emerald-600",
  red: "bg-red-50 text-red-600",
  amber: "bg-amber-50 text-amber-600",
};

const numberFormat = new Intl.NumberFormat("es-PE");

function KpiCard({
  title,
  value,
  icon: Icon,
  tone,
  subtitle,
  children,
}: {
  title: string;
  value: string;
  icon: LucideIcon;
  tone: KpiTone;
  subtitle?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
            {value}
          </p>
        </div>
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
            toneStyles[tone],
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {subtitle ? (
        <div className="mt-4 text-xs text-slate-500">{subtitle}</div>
      ) : null}
      {children}
    </Card>
  );
}

function RiskLegendItem({
  icon: Icon,
  label,
  color,
}: {
  icon: LucideIcon;
  label: string;
  color: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
      <Icon className={cn("h-3.5 w-3.5", color)} />
      {label}
    </span>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index} className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-4">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-8 w-24" />
              </div>
              <Skeleton className="h-10 w-10 rounded-full" />
            </div>
            <Skeleton className="mt-5 h-2 w-full" />
          </Card>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="p-6">
          <Skeleton className="h-4 w-52" />
          <Skeleton className="mt-2 h-3 w-64" />
          <Skeleton className="mt-6 h-72 w-full" />
        </Card>
        <Card className="p-6">
          <Skeleton className="h-4 w-56" />
          <Skeleton className="mt-2 h-3 w-64" />
          <Skeleton className="mt-6 h-72 w-full" />
        </Card>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: meta } = useMeta();
  const [facultyId, setFacultyId] = useState<number | undefined>(undefined);

  const facultiesQuery = useQuery({
    queryKey: ["faculties"],
    queryFn: api.faculties,
    staleTime: 5 * 60 * 1000,
  });

  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary", facultyId ?? "all"],
    queryFn: () => api.dashboardSummary(facultyId),
    placeholderData: keepPreviousData,
  });

  const trendQuery = useQuery({
    queryKey: ["dashboard", "trend"],
    queryFn: api.dashboardTrend,
    staleTime: 5 * 60 * 1000,
  });

  const riskQuery = useQuery({
    queryKey: ["dashboard", "risk-by-faculty"],
    queryFn: api.riskByFaculty,
    staleTime: 5 * 60 * 1000,
  });

  const faculties = facultiesQuery.data ?? [];
  const isInitialLoading =
    facultiesQuery.isPending ||
    summaryQuery.isPending ||
    trendQuery.isPending ||
    riskQuery.isPending;
  const hasError =
    facultiesQuery.isError ||
    summaryQuery.isError ||
    trendQuery.isError ||
    riskQuery.isError;
  const isRefreshing =
    summaryQuery.isFetching && !summaryQuery.isPending;

  const retryAll = () => {
    void Promise.all([
      facultiesQuery.refetch(),
      summaryQuery.refetch(),
      trendQuery.refetch(),
      riskQuery.refetch(),
    ]);
  };

  const selectedFaculty = faculties.find(
    (faculty) => faculty.id === facultyId,
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-600 shadow-sm">
            <CalendarDays className="h-4 w-4 text-slate-400" />
            Periodo {meta?.period ?? "2026-2"}
          </span>

          <div className="relative">
            <label htmlFor="faculty-filter" className="sr-only">
              Facultad
            </label>
            <select
              id="faculty-filter"
              value={facultyId?.toString() ?? ""}
              onChange={(event) =>
                setFacultyId(
                  event.target.value ? Number(event.target.value) : undefined,
                )
              }
              disabled={facultiesQuery.isPending}
              className="h-10 appearance-none rounded-lg border border-slate-200 bg-white pl-3 pr-9 text-sm font-medium text-slate-600 shadow-sm outline-none transition-colors hover:bg-slate-50 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 disabled:cursor-not-allowed disabled:text-slate-400"
            >
              <option value="">Todas las facultades</option>
              {faculties.map((faculty) => (
                <option key={faculty.id} value={faculty.id}>
                  {faculty.name}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          </div>
        </div>

        <div className="text-xs text-slate-400">
          {isRefreshing ? (
            <span className="inline-flex items-center gap-1.5">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Actualizando indicadores...
            </span>
          ) : (
            <span>Indicadores institucionales · Datos sintéticos</span>
          )}
        </div>
      </div>

      {hasError ? (
        <Card className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-semibold text-slate-900">
            No se pudieron cargar los indicadores
          </h2>
          <p className="max-w-md text-sm text-slate-500">
            Verifica que la API esté disponible en el puerto 8000 y vuelve a
            intentar.
          </p>
          <Button variant="outline" onClick={retryAll}>
            <RefreshCw className="h-4 w-4" />
            Reintentar
          </Button>
        </Card>
      ) : isInitialLoading ? (
        <DashboardSkeleton />
      ) : summaryQuery.data &&
        trendQuery.data &&
        riskQuery.data ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              title="Matrícula total"
              value={numberFormat.format(summaryQuery.data.enrollment)}
              icon={Users}
              tone="indigo"
              subtitle="Estudiantes activos en el periodo"
            />
            <KpiCard
              title="Tasa de retención global"
              value={`${(summaryQuery.data.retention_rate * 100).toFixed(1)}%`}
              icon={Percent}
              tone="emerald"
              subtitle="Derivada de la cohorte histórica sintética"
            >
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{
                    width: `${Math.min(
                      summaryQuery.data.retention_rate * 100,
                      100,
                    )}%`,
                  }}
                />
              </div>
            </KpiCard>
            <KpiCard
              title="Estudiantes en riesgo"
              value={numberFormat.format(summaryQuery.data.at_risk.count)}
              icon={ShieldAlert}
              tone="red"
              subtitle={`${(summaryQuery.data.at_risk.pct * 100).toFixed(
                1,
              )}% del total · ${summaryQuery.data.at_risk.high} alto / ${
                summaryQuery.data.at_risk.medium
              } medio`}
            />
            <KpiCard
              title="Alertas pendientes"
              value={numberFormat.format(summaryQuery.data.alerts.pending)}
              icon={BellRing}
              tone="amber"
              subtitle={
                summaryQuery.data.alerts.critical > 0 ? (
                  <span className="font-medium text-red-600">
                    {summaryQuery.data.alerts.critical} críticas sin atender
                  </span>
                ) : (
                  "Sin alertas críticas"
                )
              }
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <Card className="p-6">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  Tendencia de deserción y riesgo
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Evolución porcentual en las últimas 8 semanas
                </p>
              </div>

              <div className="mt-6 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={trendQuery.data.weeks}
                    margin={{ top: 8, right: 8, left: -18, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e2e8f0"
                    />
                    <XAxis
                      dataKey="week"
                      tickFormatter={(value) => `Sem ${value}`}
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(value) => `${value}%`}
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                      width={48}
                    />
                    <Tooltip
                      cursor={{ stroke: "#cbd5e1", strokeDasharray: "4 4" }}
                      contentStyle={{
                        borderRadius: 12,
                        borderColor: "#e2e8f0",
                        fontSize: 12,
                        boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                      }}
                      labelFormatter={(label) => `Semana ${label}`}
                      formatter={(value, name) => [
                        `${Number(value).toFixed(1)}%`,
                        name,
                      ]}
                    />
                    <Line
                      type="monotone"
                      dataKey="real_dropout_pct"
                      name="% Deserción real"
                      stroke="#4f46e5"
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: "#4f46e5" }}
                      activeDot={{ r: 5 }}
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="projected_risk_pct"
                      name="% Riesgo proyectado"
                      stroke="#f43f5e"
                      strokeWidth={2.5}
                      strokeDasharray="5 5"
                      dot={{ r: 3, fill: "#f43f5e" }}
                      activeDot={{ r: 5 }}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="mt-4 flex items-center justify-center gap-6 text-xs text-slate-500">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-indigo-600" />
                  % Deserción real
                </span>
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-rose-500" />
                  % Riesgo proyectado
                </span>
              </div>
            </Card>

            <Card className="p-6">
              <div>
                <h2 className="text-base font-semibold text-slate-900">
                  Distribución de niveles de riesgo
                </h2>
                <p className="mt-1 text-xs text-slate-500">
                  Clasificación por facultad académica
                  {selectedFaculty
                    ? ` · ${selectedFaculty.name} resaltada`
                    : ""}
                </p>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
                <RiskLegendItem
                  icon={AlertTriangle}
                  label="Riesgo alto"
                  color="text-red-500"
                />
                <RiskLegendItem
                  icon={CircleAlert}
                  label="Riesgo medio"
                  color="text-amber-500"
                />
                <RiskLegendItem
                  icon={ShieldCheck}
                  label="Riesgo bajo"
                  color="text-emerald-500"
                />
              </div>

              <div className="mt-3 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={riskQuery.data.faculties}
                    margin={{ top: 8, right: 8, left: -18, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e2e8f0"
                    />
                    <XAxis
                      dataKey="name"
                      interval={0}
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      allowDecimals={false}
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      axisLine={false}
                      tickLine={false}
                      width={48}
                    />
                    <Tooltip
                      cursor={{ fill: "#f8fafc" }}
                      contentStyle={{
                        borderRadius: 12,
                        borderColor: "#e2e8f0",
                        fontSize: 12,
                        boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
                      }}
                      formatter={(value, name) => [value, name]}
                    />
                    <Bar
                      dataKey="high"
                      stackId="risk"
                      isAnimationActive={false}
                      name="Riesgo alto"
                      fill="#ef4444"
                    >
                      {riskQuery.data.faculties.map((faculty) => (
                        <Cell
                          key={faculty.faculty_id}
                          fillOpacity={
                            facultyId === undefined ||
                            facultyId === faculty.faculty_id
                              ? 1
                              : 0.25
                          }
                        />
                      ))}
                    </Bar>
                    <Bar
                      dataKey="medium"
                      stackId="risk"
                      isAnimationActive={false}
                      name="Riesgo medio"
                      fill="#f59e0b"
                    >
                      {riskQuery.data.faculties.map((faculty) => (
                        <Cell
                          key={faculty.faculty_id}
                          fillOpacity={
                            facultyId === undefined ||
                            facultyId === faculty.faculty_id
                              ? 1
                              : 0.25
                          }
                        />
                      ))}
                    </Bar>
                    <Bar
                      dataKey="low"
                      stackId="risk"
                      isAnimationActive={false}
                      name="Riesgo bajo"
                      fill="#10b981"
                      radius={[4, 4, 0, 0]}
                    >
                      {riskQuery.data.faculties.map((faculty) => (
                        <Cell
                          key={faculty.faculty_id}
                          fillOpacity={
                            facultyId === undefined ||
                            facultyId === faculty.faculty_id
                              ? 1
                              : 0.25
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}
