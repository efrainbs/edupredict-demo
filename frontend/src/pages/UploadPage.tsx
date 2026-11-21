import { useRef, useState, type DragEvent } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Download,
  Eye,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
  UploadCloud,
  X,
} from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  api,
  type PipelineStep,
  type RiskDistribution,
  type UploadResult,
} from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const MAX_FILE_BYTES = 5 * 1024 * 1024;
const numberFormat = new Intl.NumberFormat("es-PE");

const distributionMeta: {
  key: keyof RiskDistribution;
  label: string;
  bar: string;
  text: string;
}[] = [
  { key: "high", label: "Alto", bar: "bg-red-500", text: "text-red-600" },
  { key: "medium", label: "Medio", bar: "bg-amber-500", text: "text-amber-600" },
  { key: "low", label: "Bajo", bar: "bg-emerald-500", text: "text-emerald-600" },
];

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(0)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function PipelineSteps({ steps }: { steps: PipelineStep[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {steps.map((step, index) => (
        <div
          key={step.key}
          className="rounded-lg border border-slate-100 bg-slate-50/70 p-4"
        >
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-[11px] font-semibold text-emerald-700">
              {index + 1}
            </span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-semibold text-slate-800">
              {step.label}
            </span>
          </div>
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            {step.detail}
          </p>
        </div>
      ))}
    </div>
  );
}

function Distribution({
  title,
  distribution,
  total,
}: {
  title: string;
  distribution: RiskDistribution;
  total: number;
}) {
  return (
    <div className="rounded-lg border border-slate-100 p-4">
      <p className="text-sm font-semibold text-slate-800">{title}</p>
      <div className="mt-3 space-y-2">
        {distributionMeta.map((item) => {
          const value = distribution[item.key];
          const pct = total > 0 ? (value / total) * 100 : 0;
          return (
            <div key={item.key} className="flex items-center gap-3">
              <span className="w-12 text-xs font-medium text-slate-500">
                {item.label}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={cn("h-full rounded-full", item.bar)}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span
                className={cn(
                  "w-16 text-right text-xs font-semibold tabular-nums",
                  item.text,
                )}
              >
                {numberFormat.format(value)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function DistributionComparison({ result }: { result: UploadResult }) {
  const beforeTotal = Object.values(result.distribution_before).reduce(
    (sum, value) => sum + value,
    0,
  );
  const afterTotal = Object.values(result.distribution_after).reduce(
    (sum, value) => sum + value,
    0,
  );

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">
            Distribución de riesgo
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Comparación antes y después de la carga.
          </p>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-medium text-indigo-700">
          <ArrowRight className="h-3 w-3" />
          Recalculado con el modelo activo
        </span>
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <Distribution
          title="Antes"
          distribution={result.distribution_before}
          total={beforeTotal}
        />
        <Distribution
          title="Después"
          distribution={result.distribution_after}
          total={afterTotal}
        />
      </div>
    </Card>
  );
}

function ModelView({ result }: { result: UploadResult }) {
  return (
    <Card className="p-6">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
          <Eye className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-slate-900">
            Lo que ve el modelo
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Tres filas de <code className="text-xs">student_features</code> ya
            seudonimizadas. Sin nombre, código ni DNI.
          </p>
        </div>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-3 py-2 font-semibold">pseudo_id</th>
              <th className="px-3 py-2 font-semibold">gpa_avg</th>
              <th className="px-3 py-2 font-semibold">attendance_rate</th>
              <th className="px-3 py-2 font-semibold">lms_participation</th>
              <th className="px-3 py-2 font-semibold">tuition_debt_months</th>
              <th className="px-3 py-2 font-semibold">failed_courses</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-slate-600">
            {result.model_view_sample.map((row) => (
              <tr key={row.pseudo_id}>
                <td className="px-3 py-2 text-indigo-700">{row.pseudo_id}</td>
                <td className="px-3 py-2">{row.gpa_avg.toFixed(2)}</td>
                <td className="px-3 py-2">{row.attendance_rate.toFixed(2)}</td>
                <td className="px-3 py-2">{row.lms_participation.toFixed(2)}</td>
                <td className="px-3 py-2">{row.tuition_debt_months}</td>
                <td className="px-3 py-2">{row.failed_courses}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function UploadResultView({
  result,
  onReset,
}: {
  result: UploadResult;
  onReset: () => void;
}) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          <div>
            <p className="text-sm font-semibold text-emerald-900">
              Carga procesada correctamente
            </p>
            <p className="text-xs text-emerald-700">
              Ejecución #{result.run_id} · Los riesgos y alertas se
              actualizaron.
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={onReset}>
          Cargar otro archivo
        </Button>
      </div>

      <Card className="p-6">
        <h2 className="text-base font-semibold text-slate-900">
          Pipeline de carga
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Cinco pasos desde la ingesta hasta la actualización de alertas.
        </p>
        <div className="mt-5">
          <PipelineSteps steps={result.steps} />
        </div>
      </Card>

      {result.errors.length > 0 ? (
        <Card className="p-6">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            <h2 className="text-base font-semibold text-slate-900">
              Filas rechazadas
            </h2>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            {result.errors.length} fila
            {result.errors.length === 1 ? "" : "s"} no se procesó. El resto del
            archivo sí se cargó.
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead className="bg-slate-50 text-[10px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-3 py-2 font-semibold">Fila</th>
                  <th className="px-3 py-2 font-semibold">Columna</th>
                  <th className="px-3 py-2 font-semibold">Motivo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.errors.map((error) => (
                  <tr key={`${error.row}-${error.column}`}>
                    <td className="px-3 py-2 font-mono text-xs text-slate-500">
                      {error.row}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-slate-700">
                      {error.column}
                    </td>
                    <td className="px-3 py-2 text-slate-600">{error.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}

      <DistributionComparison result={result} />
      <ModelView result={result} />
    </div>
  );
}

export function UploadPage() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const mutation = useMutation({
    mutationFn: api.uploadCsv,
    onSuccess: () => {
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["students"] }),
        queryClient.invalidateQueries({ queryKey: ["tutor", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["student"] }),
      ]);
    },
  });

  const chooseFile = (candidate: File | undefined) => {
    if (!candidate) {
      return;
    }
    setLocalError(null);
    mutation.reset();
    if (!candidate.name.toLowerCase().endsWith(".csv")) {
      setLocalError("El archivo debe tener extensión .csv.");
      setFile(null);
      return;
    }
    if (candidate.size > MAX_FILE_BYTES) {
      setLocalError("El archivo supera el límite de 5 MB.");
      setFile(null);
      return;
    }
    setFile(candidate);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  };

  const reset = () => {
    setFile(null);
    setLocalError(null);
    mutation.reset();
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  const downloadTemplate = async () => {
    setTemplateError(null);
    setDownloading(true);
    try {
      const blob = await api.uploadTemplate();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "edupredict_template.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setTemplateError(
        error instanceof Error ? error.message : "No se pudo descargar.",
      );
    } finally {
      setDownloading(false);
    }
  };

  if (mutation.isSuccess && mutation.data) {
    return (
      <UploadResultView result={mutation.data} onReset={reset} />
    );
  }

  const uploadError =
    mutation.isError && mutation.error instanceof Error
      ? mutation.error.message
      : null;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <h1 className="text-lg font-semibold text-slate-900">
              Carga de datos institucionales
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Sube un CSV con indicadores del periodo. Los identificadores se
              reemplazan por seudónimos antes de puntuar y el modelo solo ve
              variables académicas y contextuales.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={downloadTemplate}
            disabled={downloading}
          >
            {downloading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Descargar plantilla
          </Button>
        </div>
        {templateError ? (
          <p className="mt-3 text-sm text-red-600">{templateError}</p>
        ) : null}
      </Card>

      <Card className="p-6">
        <div
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
            dragging
              ? "border-indigo-400 bg-indigo-50/60"
              : "border-slate-200 bg-slate-50/60 hover:border-indigo-300 hover:bg-indigo-50/30",
          )}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white text-indigo-600 shadow-sm">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="mt-4 text-sm font-semibold text-slate-800">
            Arrastra tu archivo CSV aquí
          </p>
          <p className="mt-1 text-xs text-slate-500">
            o haz clic para seleccionarlo · UTF-8 · máx. 5 MB
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />
        </div>

        {file ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <FileSpreadsheet className="h-5 w-5 shrink-0 text-emerald-600" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800">
                  {file.name}
                </p>
                <p className="text-xs text-slate-500">
                  {formatFileSize(file.size)}
                </p>
              </div>
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  reset();
                }}
                className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                aria-label="Quitar archivo"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <Button
              onClick={() => mutation.mutate(file)}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UploadCloud className="h-4 w-4" />
              )}
              {mutation.isPending ? "Procesando..." : "Procesar archivo"}
            </Button>
          </div>
        ) : null}

        {localError ? (
          <p
            role="alert"
            className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {localError}
          </p>
        ) : null}

        {uploadError ? (
          <div
            role="alert"
            className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3"
          >
            <div className="flex items-start gap-2 text-sm text-red-700">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutation.reset()}
            >
              <RefreshCw className="h-4 w-4" />
              Reintentar
            </Button>
          </div>
        ) : null}
      </Card>

      <Card className="border-indigo-100 bg-indigo-50/50 p-5">
        <p className="text-sm text-indigo-900">
          <strong>Qué ocurre al procesar:</strong> las filas válidas actualizan
          a los estudiantes existentes por código y crean los nuevos. Las filas
          inválidas se rechazan sin detener la carga. Después se recalculan los
          riesgos con los umbrales del modelo activo.
        </p>
      </Card>
    </div>
  );
}
