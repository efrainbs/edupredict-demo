import { useState, type FormEvent } from "react";
import {
  ArrowRight,
  GraduationCap,
  Loader2,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useMeta } from "@/api/hooks";
import { DemoBanner } from "@/components/DemoBanner";
import { FullPageLoading } from "@/components/FullPageLoading";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { homePathForRole, useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const demoUsers = [
  {
    label: "Directivo",
    name: "Dirección Académica",
    email: "director@edupredict.demo",
  },
  {
    label: "Tutor 1",
    name: "Prof. Roberto Díaz",
    email: "tutor1@edupredict.demo",
  },
  {
    label: "Tutor 2",
    name: "Prof. Mariela Salazar",
    email: "tutor2@edupredict.demo",
  },
];

export function LoginPage() {
  const { user, isLoading, login } = useAuth();
  const { data: meta } = useMeta();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  const [email, setEmail] = useState("director@edupredict.demo");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isLoading) {
    return <FullPageLoading />;
  }

  if (user) {
    return <Navigate to={homePathForRole(user.role)} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const loggedUser = await login(email.trim(), password);
      navigate(from ?? homePathForRole(loggedUser.role), { replace: true });
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "No se pudo iniciar sesión. Intenta nuevamente.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <DemoBanner />

      <div className="flex min-h-[calc(100vh-2rem)] items-center justify-center px-6 py-10">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:grid-cols-[1.05fr_1fr]">
          <div className="hidden bg-gradient-to-br from-indigo-600 via-indigo-700 to-indigo-900 p-10 text-white lg:flex lg:flex-col lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15">
                <GraduationCap className="h-5 w-5" />
              </div>
              <div>
                <p className="font-semibold">EduPredict AI</p>
                <p className="text-xs text-indigo-200">Riesgo académico</p>
              </div>
            </div>

            <div className="space-y-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-200">
                Acompañamiento oportuno
              </p>
              <h1 className="max-w-sm text-3xl font-semibold leading-tight">
                Detecta señales a tiempo. Acompaña mejor.
              </h1>
              <p className="max-w-sm text-sm leading-6 text-indigo-100">
                Predicción de riesgo con datos sintéticos para priorizar el
                acompañamiento de tutores y equipos académicos.
              </p>
            </div>

            <div className="rounded-xl border border-white/15 bg-white/10 p-4 text-xs leading-5 text-indigo-50">
              <div className="flex items-center gap-2 font-medium">
                <ShieldCheck className="h-4 w-4" />
                Control de acceso por rol
              </div>
              <p className="mt-2 text-indigo-100">
                El directivo ve agregados institucionales. Cada tutor accede
                únicamente a sus estudiantes.
              </p>
            </div>
          </div>

          <div className="p-8 lg:p-10">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
                <GraduationCap className="h-5 w-5" />
              </div>
              <div>
                <p className="font-semibold">EduPredict AI</p>
                <p className="text-xs text-slate-500">Riesgo académico</p>
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
                {meta?.institution ?? "Instituto Superior Andino (demo)"}
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Inicia sesión
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Accede con tu cuenta institucional de demostración.
              </p>
            </div>

            <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-slate-700"
                >
                  Correo institucional
                </label>
                <div className="relative mt-1.5">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="username"
                    className="pl-10"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-slate-700"
                >
                  Contraseña
                </label>
                <div className="relative mt-1.5">
                  <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    className="pl-10"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                </div>
              </div>

              {error ? (
                <div
                  role="alert"
                  className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                >
                  {error}
                </div>
              ) : null}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4" />
                )}
                {isSubmitting ? "Ingresando..." : "Ingresar"}
              </Button>
            </form>

            <div className="mt-7 border-t border-slate-100 pt-6">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Acceso rápido demo
              </p>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                {demoUsers.map((demoUser) => {
                  const isSelected = email === demoUser.email;
                  return (
                    <button
                      key={demoUser.email}
                      type="button"
                      onClick={() => {
                        setEmail(demoUser.email);
                        setPassword("demo1234");
                        setError(null);
                      }}
                      className={cn(
                        "rounded-lg border px-3 py-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500",
                        isSelected
                          ? "border-indigo-200 bg-indigo-50"
                          : "border-slate-200 bg-white hover:bg-slate-50",
                      )}
                    >
                      <span className="block text-xs font-semibold text-slate-800">
                        {demoUser.label}
                      </span>
                      <span className="mt-0.5 block truncate text-[11px] text-slate-500">
                        {demoUser.name}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="mt-3 text-xs text-slate-400">
                Contraseña demo:{" "}
                <span className="font-mono text-slate-600">demo1234</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
