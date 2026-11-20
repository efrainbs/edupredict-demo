import { Loader2 } from "lucide-react";

export function FullPageLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-500">
        <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
        Cargando EduPredict...
      </div>
    </div>
  );
}
