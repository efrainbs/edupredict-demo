import { useEffect } from "react";
import { CheckCircle2, X } from "lucide-react";

export function Toast({
  message,
  onClose,
}: {
  message: string | null;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!message) {
      return;
    }
    const timeout = window.setTimeout(onClose, 5000);
    return () => window.clearTimeout(timeout);
  }, [message, onClose]);

  if (!message) {
    return null;
  }

  return (
    <div
      role="status"
      className="fixed bottom-6 right-6 z-50 flex w-full max-w-sm items-start gap-3 rounded-xl border border-emerald-200 bg-white p-4 shadow-lg"
    >
      <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-slate-900">
          Intervención registrada
        </p>
        <p className="mt-0.5 text-sm text-slate-600">{message}</p>
      </div>
      <button
        type="button"
        onClick={onClose}
        className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
        aria-label="Cerrar notificación"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
