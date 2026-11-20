import { useQuery } from "@tanstack/react-query";

import type { components } from "./api/schema";

type Meta = components["schemas"]["MetaResponse"];

const fallbackBanner = "Datos de demostración (sintéticos) — no representan estudiantes reales";

async function fetchMeta(): Promise<Meta> {
  const response = await fetch("/api/meta");
  if (!response.ok) {
    throw new Error("No se pudo cargar la información de la demo");
  }
  return response.json();
}

export default function App() {
  const { data, isError } = useQuery({ queryKey: ["meta"], queryFn: fetchMeta });
  const banner = data?.banner ?? fallbackBanner;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="bg-indigo-600 px-4 py-2 text-center text-xs font-medium text-white">
        {banner}
      </div>

      <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-16">
        <header className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-lg font-bold text-white">
            EP
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">EduPredict AI</h1>
            <p className="text-sm text-slate-500">
              {data?.institution ?? "Instituto Superior Andino (demo)"} · Periodo{" "}
              {data?.period ?? "2026-2"}
            </p>
          </div>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">
            Hito 0 · Esqueleto
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Base lista para la demo
          </h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            Backend FastAPI, frontend React y tipos generados desde OpenAPI. El siguiente
            paso es cargar los datos sintéticos de la institución.
          </p>

          {isError ? (
            <p className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              No se pudo conectar con la API. Verifica que el backend esté disponible en
              http://localhost:8000.
            </p>
          ) : (
            <p className="mt-6 text-sm text-emerald-700">
              API conectada: datos de demostración disponibles.
            </p>
          )}
        </section>
      </main>
    </div>
  );
}
