import {
  BrainCircuit,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  UploadCloud,
  Users,
  type LucideIcon,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useMeta } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { DemoBanner } from "@/components/DemoBanner";
import { roleLabel, useAuth } from "@/lib/auth";
import { initials } from "@/lib/format";
import { cn } from "@/lib/utils";

type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
};

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard Ejecutivo",
  "/upload": "Carga de datos",
  "/model": "Panel de modelo",
  "/students": "Mis estudiantes",
};

function NavSection({
  title,
  items,
}: {
  title: string;
  items: NavItem[];
}) {
  return (
    <div>
      <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </p>
      <nav className="mt-2 space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const { data: meta } = useMeta();
  const location = useLocation();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  const userItems: NavItem[] =
    user.role === "director"
      ? [
          {
            to: "/dashboard",
            label: "Dashboard Ejecutivo",
            icon: LayoutDashboard,
          },
        ]
      : [{ to: "/students", label: "Mis estudiantes", icon: Users }];

  const institutionItems: NavItem[] =
    user.role === "director"
      ? [
          { to: "/upload", label: "Carga de datos", icon: UploadCloud },
          { to: "/model", label: "Modelo", icon: BrainCircuit },
        ]
      : [];

  const title = /^\/students\/[^/]+$/.test(location.pathname)
    ? "Detalle de estudiante"
    : pageTitles[location.pathname] ?? "EduPredict";

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <DemoBanner />
      <div className="flex flex-1">
        <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
          <div className="flex h-16 items-center gap-3 border-b border-slate-100 px-6">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <GraduationCap className="h-5 w-5" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold">EduPredict AI</p>
              <p className="text-xs text-slate-500">Riesgo académico</p>
            </div>
          </div>

          <div className="flex-1 space-y-7 px-4 py-6">
            <NavSection title="Vistas de usuario" items={userItems} />
            {institutionItems.length > 0 ? (
              <NavSection
                title="Gestión institucional"
                items={institutionItems}
              />
            ) : null}
          </div>

          <div className="border-t border-slate-100 px-4 py-4">
            <div className="flex items-center gap-3 rounded-lg px-2 py-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
                {initials(user.name)}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800">
                  {user.name}
                </p>
                <p className="text-xs text-slate-500">{roleLabel(user.role)}</p>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-8">
            <div>
              <h1 className="text-base font-semibold text-slate-900">
                {title}
              </h1>
              <p className="text-xs text-slate-500">
                {meta?.institution ?? "Instituto Superior Andino (demo)"} ·
                Periodo {meta?.period ?? "2026-2"}
              </p>
            </div>

            <div className="flex items-center gap-5">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
                  {initials(user.name)}
                </div>
                <div className="leading-tight">
                  <p className="text-sm font-medium text-slate-800">
                    {user.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {roleLabel(user.role)}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  logout();
                  navigate("/login", { replace: true });
                }}
              >
                <LogOut className="h-4 w-4" />
                Cerrar sesión
              </Button>
            </div>
          </header>

          <main className="flex-1 p-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
