import { useCallback, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  Briefcase,
  CalendarCheck,
  CalendarClock,
  ClipboardList,
  GraduationCap,
  HeartHandshake,
  HeartPulse,
  Info,
  Monitor,
  Plus,
  RefreshCw,
  ShieldX,
  TrendingUp,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  ApiError,
  api,
  type InterventionType,
  type RiskLevel,
  type StudentDetail,
} from "@/api/client";
import { InterventionDialog } from "@/components/InterventionDialog";
import { RiskBadge } from "@/components/RiskBadge";
import { Toast } from "@/components/Toast";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime, initials, relativeTime } from "@/lib/format";
import { interventionByType } from "@/lib/interventions";
import { cn } from "@/lib/utils";

const riskBarStyles: Record<RiskLevel, string> = {
  alto: "bg-red-500",
  medio: "bg-amber-500",
  bajo: "bg-emerald-500",
};

const factorGroupIcons: Record<string, LucideIcon> = {
  Rendimiento: BookOpen,
  Asistencia: CalendarCheck,
  "Participación LMS": Monitor,
  "Económico / Laboral": Wallet,
  Socioemocional: HeartHandshake,
};

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-4 w-44" />
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <Skeleton className="h-14 w-14 rounded-full" />
            <div className="space-y-3">
              <Skeleton className="h-7 w-56" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-64" />
            </div>
          </div>
          <div className="space-y-3">
            <Skeleton className="h-6 w-28 rounded-full" />
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-2 w-40" />
          </div>
        </div>
      </Card>
      <Skeleton className="h-20 w-full rounded-xl" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <Card className="p-6">
            <Skeleton className="h-5 w-56" />
            <Skeleton className="mt-2 h-3 w-72" />
            <div className="mt-6 space-y-4">
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-20 w-full" />
              ))}
            </div>
          </Card>
          <Card className="p-6">
            <Skeleton className="h-5 w-44" />
            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Array.from({ length: 7 }).map((_, index) => (
                <Skeleton key={index} className="h-20 w-full" />
              ))}
            </div>
          </Card>
        </div>
        <Card className="h-fit p-6">
          <Skeleton className="h-5 w-44" />
          <Skeleton className="mt-2 h-3 w-56" />
          <div className="mt-6 space-y-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <Skeleton key={index} className="h-24 w-full" />
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function AccessDenied() {
  const navigate = useNavigate();
  return (
    <Card className="flex flex-col items-center justify-center gap-3 px-6 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-600">
        <ShieldX className="h-7 w-7" />
      </div>
      <h1 className="text-xl font-semibold text-slate-900">
        No tienes acceso a este estudiante
      </h1>
      <p className="max-w-md text-sm text-slate-500">
        Este estudiante pertenece a otro tutor. Solo el tutor responsable puede
        consultar su ficha y registrar intervenciones.
      </p>
      <Button onClick={() => navigate("/students")}>
        Volver a mis estudiantes
      </Button>
    </Card>
  );
}

function StudentNotFound() {
  const navigate = useNavigate();
  return (
    <Card className="flex flex-col items-center justify-center gap-3 px-6 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        <ClipboardList className="h-7 w-7" />
      </div>
      <h1 className="text-xl font-semibold text-slate-900">
        Estudiante no encontrado
      </h1>
      <p className="max-w-md text-sm text-slate-500">
        La ficha que buscas no existe o ya no está disponible.
      </p>
      <Button onClick={() => navigate("/students")}>
        Volver a mis estudiantes
      </Button>
    </Card>
  );
}

function Indicators({ detail }: { detail: StudentDetail }) {
  const { indicators } = detail;
  const items: { label: string; value: string; icon: LucideIcon }[] = [
    {
      label: "Promedio ponderado",
      value: `${indicators.gpa_avg.toFixed(1)}/20`,
      icon: GraduationCap,
    },
    {
      label: "Asistencia",
      value: `${Math.round(indicators.attendance_rate * 100)}%`,
      icon: CalendarCheck,
    },
    {
      label: "Participación LMS",
      value: `${Math.round(indicators.lms_participation * 100)}%`,
      icon: Monitor,
    },
    {
      label: "Deuda de pensión",
      value: `${indicators.tuition_debt_months} ${
        indicators.tuition_debt_months === 1 ? "mes" : "meses"
      }`,
      icon: Wallet,
    },
    {
      label: "Horas de trabajo",
      value: `${indicators.weekly_work_hours} h/sem`,
      icon: Briefcase,
    },
    {
      label: "Apoyo familiar",
      value: `${indicators.family_support}/5`,
      icon: Users,
    },
    {
      label: "Adaptación socioemocional",
      value: `${indicators.socioemotional_adaptation}/5`,
      icon: HeartPulse,
    },
  ];

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold text-slate-900">
        Indicadores actuales
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Señales académicas y contextuales del periodo en curso.
      </p>
      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.label}
              className="rounded-lg border border-slate-100 bg-slate-50/70 p-3"
            >
              <Icon className="h-4 w-4 text-slate-400" />
              <p className="mt-2 text-[11px] leading-tight text-slate-500">
                {item.label}
              </p>
              <p className="mt-1 text-lg font-semibold text-slate-900">
                {item.value}
              </p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export function StudentDetailPage() {
  const { id } = useParams();
  const studentId = Number(id);
  const isValidId = Number.isInteger(studentId) && studentId > 0;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [initialType, setInitialType] =
    useState<InterventionType>("seguimiento");
  const [toast, setToast] = useState<string | null>(null);
  const closeToast = useCallback(() => setToast(null), []);

  const detailQuery = useQuery({
    queryKey: ["student", studentId],
    queryFn: () => api.studentDetail(studentId),
    enabled: isValidId,
    retry: false,
  });

  const openIntervention = (type: InterventionType) => {
    setInitialType(type);
    setDialogOpen(true);
  };

  if (!isValidId) {
    return <StudentNotFound />;
  }

  if (detailQuery.isError) {
    if (
      detailQuery.error instanceof ApiError &&
      detailQuery.error.status === 403
    ) {
      return <AccessDenied />;
    }
    if (
      detailQuery.error instanceof ApiError &&
      detailQuery.error.status === 404
    ) {
      return <StudentNotFound />;
    }
    return (
      <Card className="flex flex-col items-center justify-center gap-3 px-6 py-20 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h1 className="text-lg font-semibold text-slate-900">
          No se pudo cargar el estudiante
        </h1>
        <p className="max-w-md text-sm text-slate-500">
          {detailQuery.error.message}
        </p>
        <Button variant="outline" onClick={() => detailQuery.refetch()}>
          <RefreshCw className="h-4 w-4" />
          Reintentar
        </Button>
      </Card>
    );
  }

  if (detailQuery.isPending || !detailQuery.data) {
    return <DetailSkeleton />;
  }

  const detail = detailQuery.data;
  const { risk, interventions } = detail;
  const maxImpact = Math.max(
    ...risk.top_factors.map((factor) => Math.abs(factor.impact)),
    0.0001,
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          to="/students"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition-colors hover:text-indigo-600"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a mis estudiantes
        </Link>
        <span className="text-xs text-slate-400">
          Actualizado {relativeTime(risk.computed_at)}
        </span>
      </div>

      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-lg font-semibold text-indigo-700">
              {initials(detail.full_name)}
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
                {detail.full_name}
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                {detail.code} · {detail.career}
              </p>
              <p className="text-sm text-slate-500">
                {detail.faculty} · Ciclo {detail.cycle}
              </p>
            </div>
          </div>

          <div className="flex flex-col items-start gap-2 sm:items-end">
            <RiskBadge level={risk.level} size="md" />
            <div className="text-left sm:text-right">
              <p className="text-xs font-medium text-slate-400">
                Puntaje de riesgo
              </p>
              <p className="text-3xl font-semibold tracking-tight text-slate-900">
                {risk.score}
                <span className="text-base font-normal text-slate-400">
                  /100
                </span>
              </p>
            </div>
            <div className="h-2 w-40 overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn(
                  "h-full rounded-full",
                  riskBarStyles[risk.level],
                )}
                style={{
                  width: `${Math.max(0, Math.min(100, risk.score))}%`,
                }}
              />
            </div>
          </div>
        </div>
      </Card>

      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>{risk.disclaimer}</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-base font-semibold text-slate-900">
              Por qué aparece esta alerta
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Factores que más influyen en el riesgo estimado del estudiante.
            </p>

            {risk.top_factors.length > 0 ? (
              <div className="mt-5 space-y-3">
                {risk.top_factors.map((factor) => {
                  const Icon = factorGroupIcons[factor.group] ?? Activity;
                  const width = Math.max(
                    4,
                    Math.round(
                      (Math.abs(factor.impact) / maxImpact) * 100,
                    ),
                  );
                  return (
                    <div
                      key={factor.feature}
                      className="rounded-lg border border-slate-100 bg-slate-50/60 p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div className="flex min-w-0 items-start gap-3">
                          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-slate-500 shadow-sm">
                            <Icon className="h-4 w-4" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-800">
                              {factor.text}
                            </p>
                            <p className="mt-0.5 text-xs text-slate-400">
                              {factor.group}
                            </p>
                          </div>
                        </div>
                        <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-600">
                          <TrendingUp className="h-3 w-3" />
                          Aumenta el riesgo
                        </span>
                      </div>
                      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200/70">
                        <div
                          className="h-full rounded-full bg-red-400"
                          style={{ width: `${width}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="mt-5 rounded-lg border border-slate-100 bg-slate-50 p-4 text-sm text-slate-500">
                No se identificaron factores de riesgo relevantes para este
                estudiante.
              </p>
            )}
          </Card>

          <Indicators detail={detail} />
        </div>

        <Card className="h-fit p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Historial de intervenciones
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {interventions.length} registro
                {interventions.length === 1 ? "" : "s"} de acompañamiento.
              </p>
            </div>
            <Button
              size="sm"
              onClick={() => openIntervention("seguimiento")}
            >
              <Plus className="h-4 w-4" />
              Registrar
            </Button>
          </div>

          {interventions.length === 0 ? (
            <div className="mt-5 rounded-lg border border-dashed border-slate-200 p-6 text-center">
              <ClipboardList className="mx-auto h-8 w-8 text-slate-300" />
              <p className="mt-2 text-sm font-medium text-slate-600">
                Sin intervenciones registradas
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Registra el primer seguimiento para iniciar el historial.
              </p>
            </div>
          ) : (
            <ol className="mt-5 space-y-4">
              {interventions.map((intervention) => {
                const meta = interventionByType[intervention.type];
                const Icon = meta.icon;
                return (
                  <li
                    key={intervention.id}
                    className="relative pl-11"
                  >
                    <div className="absolute left-0 top-0 flex h-8 w-8 items-center justify-center rounded-full bg-indigo-50 text-indigo-600">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="rounded-lg border border-slate-100 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-sm font-medium text-slate-800">
                          {meta.label}
                        </span>
                        <span className="text-xs text-slate-400">
                          {relativeTime(intervention.created_at)}
                        </span>
                      </div>
                      <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">
                        {intervention.note}
                      </p>
                      {intervention.scheduled_at ? (
                        <p className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-indigo-600">
                          <CalendarClock className="h-3.5 w-3.5" />
                          Programada para{" "}
                          {formatDateTime(intervention.scheduled_at)}
                        </p>
                      ) : null}
                      <p className="mt-2 text-xs text-slate-400">
                        {intervention.tutor_name}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
        </Card>
      </div>

      <InterventionDialog
        open={dialogOpen}
        studentId={detail.id}
        studentName={detail.full_name}
        initialType={initialType}
        onClose={() => setDialogOpen(false)}
        onSuccess={setToast}
      />

      <Toast message={toast} onClose={closeToast} />
    </div>
  );
}
