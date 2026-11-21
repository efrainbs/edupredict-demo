import type { ReactNode } from "react";
import { BrainCircuit, UploadCloud } from "lucide-react";
import {
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import { AppLayout } from "@/components/AppLayout";
import { FullPageLoading } from "@/components/FullPageLoading";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";
import { StudentDetailPage } from "@/pages/StudentDetailPage";
import { StudentsPage } from "@/pages/StudentsPage";
import { homePathForRole, useAuth } from "@/lib/auth";

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullPageLoading />;
  }
  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname }}
      />
    );
  }
  return children;
}

function RoleRoute({
  role,
  children,
}: {
  role: "director" | "tutor";
  children: ReactNode;
}) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <FullPageLoading />;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role !== role) {
    return <Navigate to={homePathForRole(user.role)} replace />;
  }
  return children;
}

function IndexRedirect() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <FullPageLoading />;
  }
  return (
    <Navigate
      to={user ? homePathForRole(user.role) : "/login"}
      replace
    />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route
          path="/dashboard"
          element={
            <RoleRoute role="director">
              <DashboardPage />
            </RoleRoute>
          }
        />
        <Route
          path="/upload"
          element={
            <RoleRoute role="director">
              <PlaceholderPage
                icon={UploadCloud}
                title="Carga de datos"
                description="La carga de CSV, el pipeline por pasos y la actualización de riesgos se habilitan en el siguiente avance de la demo."
              />
            </RoleRoute>
          }
        />
        <Route
          path="/model"
          element={
            <RoleRoute role="director">
              <PlaceholderPage
                icon={BrainCircuit}
                title="Panel de modelo"
                description="Las métricas del modelo activo y la importancia de variables se habilitan en el siguiente avance de la demo."
              />
            </RoleRoute>
          }
        />
        <Route
          path="/students"
          element={
            <RoleRoute role="tutor">
              <StudentsPage />
            </RoleRoute>
          }
        />
        <Route
          path="/students/:id"
          element={
            <RoleRoute role="tutor">
              <StudentDetailPage />
            </RoleRoute>
          }
        />
      </Route>

      <Route path="/" element={<IndexRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
