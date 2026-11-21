import { expect, test, type Page } from "@playwright/test";
import { fileURLToPath } from "node:url";

const API = "http://127.0.0.1:8000";
const DEMO_CSV = fileURLToPath(
  new URL("../../backend/data/demo_upload.csv", import.meta.url),
);

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Correo institucional").fill(email);
  await page.getByLabel("Contraseña").fill("demo1234");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page).not.toHaveURL(/\/login$/, { timeout: 15_000 });
}

async function logout(page: Page) {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/login$/);
}

test("guion de demo completo", async ({ page, request }) => {
  await login(page, "director@edupredict.demo");
  await expect(
    page.getByRole("heading", { name: "Dashboard Ejecutivo", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Matrícula total")).toBeVisible();
  await expect(page.getByText("Tasa de retención global")).toBeVisible();

  await page.getByRole("link", { name: "Carga de datos" }).click();
  await expect(page).toHaveURL(/\/upload$/);
  await expect(
    page.getByRole("heading", { name: "Carga de datos institucionales" }),
  ).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles(DEMO_CSV);
  await page.getByRole("button", { name: "Procesar archivo" }).click();
  await expect(page.getByText("Carga procesada correctamente")).toBeVisible({
    timeout: 60_000,
  });
  await expect(page.getByText("Filas rechazadas")).toBeVisible();
  await expect(page.getByText(/3 filas no se procesó/)).toBeVisible();
  await expect(page.getByText("Pipeline de carga")).toBeVisible();

  await logout(page);

  await login(page, "tutor1@edupredict.demo");
  await expect(
    page.getByRole("heading", { name: "Mis estudiantes", level: 1 }),
  ).toBeVisible();

  await page.getByLabel("Buscar estudiante").fill("Diego Torres");
  const diegoRow = page.getByRole("row", { name: /Diego Torres Ruiz/ });
  await expect(diegoRow).toBeVisible();
  await expect(diegoRow.getByText("Riesgo alto")).toBeVisible();
  await diegoRow.getByText("Diego Torres Ruiz").click();

  await expect(
    page.getByRole("heading", { name: "Diego Torres Ruiz", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Historial de intervenciones")).toBeVisible();

  const note = `Seguimiento e2e ${Date.now()}: plan de estudio acordado.`;
  await page.getByRole("button", { name: "Registrar", exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Registrar intervención" }),
  ).toBeVisible();
  await page.getByLabel("Nota").fill(note);
  await page.getByRole("button", { name: "Guardar intervención" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Intervención registrada",
  );
  await expect(page.getByText(note)).toBeVisible();

  const tutor2Login = await request.post(`${API}/api/auth/login`, {
    data: { email: "tutor2@edupredict.demo", password: "demo1234" },
  });
  expect(tutor2Login.ok()).toBeTruthy();
  const tutor2Token = (await tutor2Login.json()).access_token as string;
  const tutor2Students = await request.get(`${API}/api/students`, {
    headers: { Authorization: `Bearer ${tutor2Token}` },
  });
  expect(tutor2Students.ok()).toBeTruthy();
  const foreignStudent = (await tutor2Students.json())[0] as { id: number };

  await page.goto(`/students/${foreignStudent.id}`);
  await expect(
    page.getByRole("heading", {
      name: "No tienes acceso a este estudiante",
      level: 1,
    }),
  ).toBeVisible();

  await page.goto("/students");
  await logout(page);

  await login(page, "director@edupredict.demo");
  await page.goto("/model");
  await expect(
    page.getByRole("main").getByRole("heading", {
      name: "Panel de modelo",
      level: 1,
    }),
  ).toBeVisible();
  await expect(page.getByText("Datos sintéticos", { exact: true })).toBeVisible();
  await expect(page.getByText("PR-AUC", { exact: true })).toBeVisible();
});

test("404 amigable y atajo de búsqueda", async ({ page }) => {
  await page.goto("/ruta-inexistente");
  await expect(
    page.getByRole("heading", { name: "Página no encontrada", level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Error 404")).toBeVisible();
  await expect(page.getByRole("link", { name: "Volver al inicio" })).toBeVisible();

  await login(page, "tutor1@edupredict.demo");
  await expect(
    page.getByRole("heading", { name: "Mis estudiantes", level: 1 }),
  ).toBeVisible();
  await page.keyboard.press("/");
  await expect(page.getByLabel("Buscar estudiante")).toBeFocused();
});
