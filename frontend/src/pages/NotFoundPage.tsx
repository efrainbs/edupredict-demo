import { ArrowLeft, GraduationCap, SearchX } from "lucide-react";
import { Link } from "react-router-dom";

import { DemoBanner } from "@/components/DemoBanner";

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <DemoBanner />
      <div className="flex flex-1 items-center justify-center px-6 py-16">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white">
            <GraduationCap className="h-6 w-6" />
          </div>
          <div className="mx-auto mt-6 flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500">
            <SearchX className="h-7 w-7" />
          </div>
          <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-indigo-600">
            Error 404
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            Página no encontrada
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            La dirección que abriste no existe o cambió. Vuelve al inicio para
            continuar con la demo.
          </p>
          <Link
            to="/"
            className="mt-6 inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al inicio
          </Link>
        </div>
      </div>
    </div>
  );
}
