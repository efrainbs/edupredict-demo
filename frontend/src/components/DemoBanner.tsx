import { useMeta } from "@/api/hooks";

const fallbackBanner =
  "Datos de demostración (sintéticos) — no representan estudiantes reales";

export function DemoBanner() {
  const { data } = useMeta();

  return (
    <div className="bg-indigo-600 px-4 py-2 text-center text-xs font-medium text-white">
      {data?.banner ?? fallbackBanner}
    </div>
  );
}
