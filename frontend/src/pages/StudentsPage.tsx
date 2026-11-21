import { useCallback, useState, type KeyboardEvent } from "react";
import {
  AlertTriangle,
  Loader2,
  RefreshCw,
  Search,
  SearchX,
  Users,
} from "lucide-react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import {
  api,
  type InterventionType,
  type RiskLevel,
  type StudentListItem,
  type TutorSummary,
} from "@/api/client";
import { InterventionDialog } from "@/components/InterventionDialog";
import { RiskBadge } from "@/components/RiskBadge";
import { Toast } from "@/components/Toast";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import { firstName, initials, relativeTime } from "@/lib/format";
import { useDebouncedValue } from "@/lib/use-debounced-value";
import { cn } from "@/lib/utils";

const riskFilters: { value: "all" | RiskLevel; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "alto", label: "Alto" },
  { value: "medio", label: "Medio" },
  { value: "bajo", label: "Bajo" },
];

function TutorBanner({
  summary,
  tutorName,
  loading,
}: {
  summary: TutorSummary | undefined;
  tutorName: string;
  loading: boolean;
}) {
  if (loading) {
    return (
      <Card className="border-0 bg-indigo-700 p-6">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <Skeleton className="h-12 w-12 rounded-xl bg-white/20" />
            <div className="space-y-3">
              <Skeleton className="h-3 w-28 bg-white/20" />
              <Skeleton className="h-6 w-80 bg-white/20" />
              <Skeleton className="h-3 w-64 bg-white/20" />
            </div>
          </div>
          <Skeleton className="h-20 w-72 bg-white/20" />
        </div>
      </Card>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-700 p-6 text-white shadow-lg">
      <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-white/10" />
      <div className="pointer-events-none absolute -bottom-24 right-24 h-44 w-44 rounded-full bg-white/5" />
      <div className="relative flex flex-wrap items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/15">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-indigo-100">
              Hola, {firstName(tutorName)}
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
              Tus estudiantes requieren acompañamiento
            </h1>
            <p className="mt-1 max-w-xl text-sm text-indigo-100">
              Tienes {summary.in_observation} estudiantes en observación y{" "}
              {summary.critical_pending} alertas críticas pendientes.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6 rounded-xl bg-white/10 px-5 py-4 backdrop-blur-sm">
          <div>
            <p className="text-xs font-medium text-indigo-100">
              En observación
            </p>
            <p className="mt-1 text-2xl font-semibold">
              {summary.in_observation}
            </p>
          </div>
          <div className="h-10 w-px bg-white/20" />
          <div>
            <p className="text-xs font-medium text-indigo-100">
              Alertas críticas
            </p>
            <p
              className={cn(
                "mt-1 text-2xl font-semibold",
                summary.critical_pending > 0 ? "text-red-200" : "text-white",
              )}
            >
              {summary.critical_pending}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}

function StudentRow({
  student,
  onOpen,
  onAction,
}: {
  student: StudentListItem;
  onOpen: () => void;
  onAction: (type: InterventionType) => void;
}) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTableRowElement>) => {
    if (event.target !== event.currentTarget) {
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onOpen();
    }
  };

  return (
    <tr
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={handleKeyDown}
      className="cursor-pointer transition-colors hover:bg-slate-50 focus:bg-indigo-50/60 focus:outline-none"
    >
      <td className="px-3 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-semibold text-indigo-700">
            {initials(student.full_name)}
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900">
              {student.full_name}
            </p>
            <p className="truncate text-xs text-slate-500">
              {student.career} · {student.code}
            </p>
          </div>
        </div>
      </td>
      <td className="px-3 py-3">
        <RiskBadge level={student.risk_level} />
      </td>
      <td className="px-3 py-3">
        <span className="text-sm text-slate-600">
          {student.main_factor ?? "Sin factor dominante"}
        </span>
      </td>
      <td className="px-3 py-3">
        {student.pending_alerts > 0 ? (
          <div className="flex items-start gap-1.5 text-red-600">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <div>
              <p className="text-xs font-medium">
                {student.pending_alerts} pendiente
                {student.pending_alerts === 1 ? "" : "s"}
              </p>
              {student.reasons.length > 0 ? (
                <p className="mt-0.5 text-xs text-slate-500">
                  {student.reasons.join(" · ")}
                </p>
              ) : null}
            </div>
          </div>
        ) : (
          <span className="text-xs text-slate-400">
            Sin alertas pendientes
          </span>
        )}
      </td>
      <td className="px-3 py-3">
        <span className="text-xs text-slate-500">
          {relativeTime(student.last_contact_at)}
        </span>
      </td>
      <td className="px-3 py-3">
        <div
          className="flex items-center justify-end gap-1"
          onClick={(event) => event.stopPropagation()}
          onKeyDown={(event) => event.stopPropagation()}
        >
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 px-2 text-[11px]"
            onClick={() => onAction("seguimiento")}
          >
            Seguimiento
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 px-2 text-[11px]"
            onClick={() => onAction("reunion")}
          >
            Agendar
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-[11px]"
            onClick={() => onAction("mensaje")}
          >
            Mensaje
          </Button>
        </div>
      </td>
    </tr>
  );
}

function StudentsTableSkeleton() {
  return (
    <div className="divide-y divide-slate-100">
      {Array.from({ length: 5 }).map((_, index) => (
        <div
          key={index}
          className="flex items-center gap-4 px-5 py-4"
        >
          <Skeleton className="h-9 w-9 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-3 w-28" />
          <Skeleton className="h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

export function StudentsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [risk, setRisk] = useState<"all" | RiskLevel>("all");
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search);
  const [dialog, setDialog] = useState<{
    student: StudentListItem;
    type: InterventionType;
  } | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const closeToast = useCallback(() => setToast(null), []);

  const summaryQuery = useQuery({
    queryKey: ["tutor", "summary"],
    queryFn: api.tutorSummary,
  });

  const studentsQuery = useQuery({
    queryKey: ["students", risk, debouncedSearch],
    queryFn: () =>
      api.students({
        risk: risk === "all" ? undefined : risk,
        q: debouncedSearch,
      }),
    placeholderData: keepPreviousData,
  });

  const students = studentsQuery.data ?? [];
  const hasError = summaryQuery.isError || studentsQuery.isError;
  const isInitialLoading =
    summaryQuery.isPending || studentsQuery.isPending;
  const isRefreshing = studentsQuery.isFetching && !studentsQuery.isPending;

  const retryAll = () => {
    void Promise.all([summaryQuery.refetch(), studentsQuery.refetch()]);
  };

  const openDialog = (
    student: StudentListItem,
    type: InterventionType,
  ) => {
    setDialog({ student, type });
  };

  return (
    <div className="space-y-6">
      <TutorBanner
        summary={summaryQuery.data}
        tutorName={summaryQuery.data?.tutor_name ?? user?.name ?? "Tutor"}
        loading={summaryQuery.isPending}
      />

      {hasError ? (
        <Card className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <h2 className="text-lg font-semibold text-slate-900">
            No se pudieron cargar tus estudiantes
          </h2>
          <p className="max-w-md text-sm text-slate-500">
            Verifica que la API esté disponible y vuelve a intentar.
          </p>
          <Button variant="outline" onClick={retryAll}>
            <RefreshCw className="h-4 w-4" />
            Reintentar
          </Button>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">
                Mis estudiantes
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Ordenados por nivel de riesgo y probabilidad.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por nombre o código..."
                  aria-label="Buscar estudiante"
                  className="h-9 w-64 pl-9"
                />
              </div>

              <div
                role="group"
                aria-label="Filtrar por nivel de riesgo"
                className="flex rounded-lg border border-slate-200 bg-slate-50 p-1"
              >
                {riskFilters.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => setRisk(filter.value)}
                    aria-pressed={risk === filter.value}
                    className={cn(
                      "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                      risk === filter.value
                        ? "bg-white text-slate-900 shadow-sm"
                        : "text-slate-500 hover:text-slate-700",
                    )}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>

              {isRefreshing ? (
                <span className="inline-flex items-center gap-1.5 text-xs text-slate-400">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Actualizando...
                </span>
              ) : null}
            </div>
          </div>

          {isInitialLoading ? (
            <StudentsTableSkeleton />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[960px] text-left">
                <thead className="bg-slate-50/80 text-[10px] uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">
                      Estudiante / Carrera
                    </th>
                    <th className="px-3 py-2.5 font-semibold">
                      Riesgo (IA)
                    </th>
                    <th className="px-3 py-2.5 font-semibold">
                      Factor principal
                    </th>
                    <th className="px-3 py-2.5 font-semibold">
                      Alertas / razones
                    </th>
                    <th className="px-3 py-2.5 font-semibold">
                      Último contacto
                    </th>
                    <th className="px-3 py-2.5 text-right font-semibold">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {students.map((student) => (
                    <StudentRow
                      key={student.id}
                      student={student}
                      onOpen={() => navigate(`/students/${student.id}`)}
                      onAction={(type) => openDialog(student, type)}
                    />
                  ))}
                </tbody>
              </table>

              {students.length === 0 ? (
                <div className="flex flex-col items-center justify-center gap-2 px-6 py-14 text-center">
                  <SearchX className="h-8 w-8 text-slate-300" />
                  <p className="text-sm font-medium text-slate-600">
                    No se encontraron estudiantes
                  </p>
                  <p className="text-xs text-slate-500">
                    Prueba con otro nombre, código o nivel de riesgo.
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </Card>
      )}

      {dialog ? (
        <InterventionDialog
          open
          studentId={dialog.student.id}
          studentName={dialog.student.full_name}
          initialType={dialog.type}
          onClose={() => setDialog(null)}
          onSuccess={setToast}
        />
      ) : null}

      <Toast message={toast} onClose={closeToast} />
    </div>
  );
}
