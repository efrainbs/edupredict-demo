import {
  AlertTriangle,
  BrainCircuit,
  CalendarDays,
  Database,
  RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api, type ModelInfo } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/format";

const numberFormat = new Intl.NumberFormat("es-PE");
const percentFormat = new Intl.NumberFormat("es-PE", {
  style: "percent",
  maximumFractionDigits: 1,
});

const metricMeta: {
  key: keyof ModelInfo["metrics"];
  label: string;
  hint: string;
}[] = [
  { key: "f1", label: "F1", hint: "Equilibrio precisión / recall" },
  { key: "precision", label: "Precisión", hint: "Alertas que se confirman" },
  { key: "recall", label: "Recall", hint: "Casos de riesgo detectados" },
  { key: "pr_auc", label: "PR-AUC", hint: "Calidad global del ranking" },
];

function ModelSkeleton() {
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <Skeleton className="h-6 w-52" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-10 w-40" />
        </div>
      </Card>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index} className="p-6">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="mt-4 h-8 w-20" />
            <Skeleton className="mt-4 h-3 w-32" />
          </Card>
        ))}
      </div>
      <Card className="p-6">
        <Skeleton className="h-5 w-64" />
        <Skeleton className="mt-6 h-80 w-full" />
      </Card>
    </div>
  );
}

function ImportanceChart({ info }: { info: ModelInfo }) {
  const data = info.feature_importance.map((item) => ({
    label: item.label,
    importance: Number((item.importance * 100).toFixed(2)),
  }));

  return (
    <Card className="p-6">
      <h2 className="text-base font-semibold text-slate-900">
        Importancia global de variables
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        Top 10 variables según el modelo XGBoost activo (% de importancia).
      </p>
      <div className="mt-5 h-96 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 24, bottom: 4, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} />
            <YAxis
              type="category"
              dataKey="label"
              width={190}
              tick={{ fontSize: 11, fill: "#334155" }}
            />
            <Tooltip
              formatter={(value) => [`${String(value)}%`, "Importancia"]}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Bar dataKey="importance" fill="#4f46e5" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function ModelPage() {
  const infoQuery = useQuery({
    queryKey: ["model", "info"],
    queryFn: api.modelInfo,
  });

  if (infoQuery.isPending) {
    return <ModelSkeleton />;
  }

  if (infoQuery.isError || !infoQuery.data) {
    return (
      <Card className="flex flex-col items-center justify-center gap-3 px-6 py-20 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50 text-red-600">
          <AlertTriangle className="h-6 w-6" />
        </div>
        <h1 className="text-lg font-semibold text-slate-900">
          No se pudo cargar el panel del modelo
        </h1>
        <p className="max-w-md text-sm text-slate-500">
          {infoQuery.error instanceof Error
            ? infoQuery.error.message
            : "Verifica que la API esté disponible y vuelve a intentar."}
        </p>
        <Button variant="outline" onClick={() => infoQuery.refetch()}>
          <RefreshCw className="h-4 w-4" />
          Reintentar
        </Button>
      </Card>
    );
  }

  const info = infoQuery.data;

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
              <BrainCircuit className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">
                Panel de modelo
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Modelo único de clasificación de riesgo de deserción.
              </p>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <BrainCircuit className="h-3.5 w-3.5" />
                  Algoritmo: <strong className="text-slate-700">{info.algorithm}</strong>
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CalendarDays className="h-3.5 w-3.5" />
                  Entrenado: {formatDateTime(info.trained_at)}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5" />
                  Registros de entrenamiento:{" "}
                  <strong className="text-slate-700">
                    {numberFormat.format(info.n_train)}
                  </strong>
                </span>
              </div>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">
            <AlertTriangle className="h-3.5 w-3.5" />
            Datos sintéticos
          </span>
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metricMeta.map((metric) => (
          <Card key={metric.key} className="p-6">
            <p className="text-sm font-medium text-slate-500">{metric.label}</p>
            <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
              {percentFormat.format(info.metrics[metric.key])}
            </p>
            <p className="mt-3 text-xs text-slate-500">{metric.hint}</p>
          </Card>
        ))}
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
        <p>{info.disclaimer}</p>
      </div>

      <ImportanceChart info={info} />
    </div>
  );
}
