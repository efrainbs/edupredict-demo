import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, X } from "lucide-react";

import { api, type InterventionCreate, type InterventionType } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { interventionTypes } from "@/lib/interventions";
import { cn } from "@/lib/utils";

function toLocalDateTimeInput(date: Date): string {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

export function InterventionDialog({
  open,
  studentId,
  studentName,
  initialType,
  onClose,
  onSuccess,
}: {
  open: boolean;
  studentId: number;
  studentName: string;
  initialType: InterventionType;
  onClose: () => void;
  onSuccess: (message: string) => void;
}) {
  const queryClient = useQueryClient();
  const [type, setType] = useState<InterventionType>(initialType);
  const [note, setNote] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    setType(initialType);
    setNote("");
    setScheduledAt("");
    setError(null);
  }, [initialType, open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose, open]);

  const mutation = useMutation({
    mutationFn: (payload: InterventionCreate) =>
      api.createIntervention(studentId, payload),
    onSuccess: () => {
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ["students"] }),
        queryClient.invalidateQueries({ queryKey: ["student", studentId] }),
        queryClient.invalidateQueries({ queryKey: ["tutor", "summary"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
      onSuccess("El historial y el estado de alertas se actualizaron.");
      onClose();
    },
    onError: (mutationError: Error) => {
      setError(mutationError.message);
    },
  });

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const trimmedNote = note.trim();
    if (!trimmedNote) {
      setError("La nota de la intervención es obligatoria.");
      return;
    }
    if (trimmedNote.length > 500) {
      setError("La nota no puede superar los 500 caracteres.");
      return;
    }

    let scheduledIso: string | null = null;
    if (type === "reunion") {
      if (!scheduledAt) {
        setError("Selecciona la fecha y hora de la reunión.");
        return;
      }
      const scheduledDate = new Date(scheduledAt);
      if (Number.isNaN(scheduledDate.getTime())) {
        setError("La fecha y hora seleccionadas no son válidas.");
        return;
      }
      if (scheduledDate.getTime() <= Date.now()) {
        setError("La reunión debe programarse para una fecha futura.");
        return;
      }
      scheduledIso = scheduledDate.toISOString();
    }

    mutation.mutate({
      type,
      note: trimmedNote,
      scheduled_at: scheduledIso,
    });
  };

  if (!open) {
    return null;
  }

  const minDateTime = toLocalDateTimeInput(new Date(Date.now() + 60_000));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Cerrar diálogo"
        className="absolute inset-0 cursor-default bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="intervention-title"
        className="relative z-10 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2
              id="intervention-title"
              className="text-lg font-semibold text-slate-900"
            >
              Registrar intervención
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {studentName} · La acción queda registrada en su historial de
              acompañamiento.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          <div>
            <p className="mb-2 text-sm font-medium text-slate-700">Tipo</p>
            <div className="grid grid-cols-3 gap-2">
              {interventionTypes.map((option) => {
                const Icon = option.icon;
                const active = type === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      setType(option.value);
                      setError(null);
                    }}
                    disabled={mutation.isPending}
                    className={cn(
                      "flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "border-indigo-200 bg-indigo-50 text-indigo-700"
                        : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                    )}
                    aria-pressed={active}
                  >
                    <Icon className="h-4 w-4" />
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label
              htmlFor="intervention-note"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Nota
            </label>
            <Textarea
              id="intervention-note"
              value={note}
              onChange={(event) => {
                setNote(event.target.value);
                setError(null);
              }}
              maxLength={500}
              placeholder={
                type === "reunion"
                  ? "Motivo de la reunión y acuerdos esperados..."
                  : "Describe la acción realizada y los acuerdos con el estudiante..."
              }
              disabled={mutation.isPending}
              autoFocus
            />
            <div className="mt-1 flex justify-between text-xs text-slate-400">
              <span>
                {type === "mensaje"
                  ? "Este registro no envía un mensaje real."
                  : "Visible para el tutor responsable."}
              </span>
              <span>{note.length}/500</span>
            </div>
          </div>

          {type === "reunion" ? (
            <div>
              <label
                htmlFor="intervention-scheduled-at"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Fecha y hora
              </label>
              <Input
                id="intervention-scheduled-at"
                type="datetime-local"
                value={scheduledAt}
                min={minDateTime}
                onChange={(event) => {
                  setScheduledAt(event.target.value);
                  setError(null);
                }}
                disabled={mutation.isPending}
              />
            </div>
          ) : null}

          {error ? (
            <p
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {error}
            </p>
          ) : null}

          <div className="flex justify-end gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={mutation.isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : null}
              Guardar intervención
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
