# MILESTONES — Hitos con criterios de aceptación

Trabajo con OpenCode: **un hito por sesión.** Empieza en modo *Plan* (el agente propone, tú revisas) y pasa a modo *Build* cuando el plan te convenza. Cada hito termina con `make test` en verde y un commit.

Prompt base (cambia el número de hito):
> Lee `AGENTS.md` y `docs/MILESTONES.md`. Implementa **solo el hito N**, leyendo únicamente los documentos que el hito cita. Al terminar ejecuta `make test`, verifica los criterios de aceptación uno por uno y resume qué hiciste y qué falta. No construyas nada fuera del hito.

---

## Hito 0 — Esqueleto
**Lee:** `AGENTS.md`.
**Tareas**
- Estructura de carpetas de `AGENTS.md`; `Makefile` con todos los targets (los que aún no apliquen pueden imprimir "pendiente").
- Backend FastAPI mínimo con `GET /api/meta` (contrato en `API_CONTRACT.md` §1) y `pytest` con un test de humo.
- Frontend Vite + React + TS + Tailwind + shadcn/ui, con proxy `/api` → `8000`, que muestre el banner de demo leyendo `/api/meta`.
- `make gen-types` genera `frontend/src/api/schema.d.ts`.
- `README.md` corto con los comandos.

**Aceptación**
- [ ] `make setup && make dev` levanta ambos servicios; `http://localhost:5173` muestra el banner "Datos de demostración (sintéticos)…".
- [ ] `make test` pasa (pytest + typecheck + build).
- [ ] `make gen-types` produce `schema.d.ts` con el tipo de `/api/meta`.

## Hito 1 — Datos sintéticos
**Lee:** `docs/DATA_MODEL.md` (§1, §2, §3, §4, §7, §8).
**Tareas**
- Modelos SQLModel de todas las tablas; creación de BD.
- `backend/ml/generate_data.py` según §3, con constantes con nombre y semilla fija.
- `make seed`: reinicia BD, crea facultades, carreras, 20 tutores, 3 usuarios demo (contraseña con bcrypt), 1,500 estudiantes (con `pseudo_id`), `student_features`, 4,000 filas de `historical_cohort`, los 5 estudiantes curados y `weekly_snapshots` provisionales.

**Aceptación**
- [ ] `make seed` corre en < 60 s y es idempotente (se puede ejecutar dos veces).
- [ ] Conteos: 1,500 estudiantes, 20 tutores, 4,000 históricos; cada tutor tiene entre 50 y 100 estudiantes.
- [ ] Prevalencia de `dropped_out` en `historical_cohort` entre 15% y 20% (test).
- [ ] **Test de seudonimización:** ninguna columna de `student_features` ni `historical_cohort` contiene nombre ni código; `pseudo_id` es determinista.
- [ ] Los 5 estudiantes curados existen y pertenecen a Tutor 1.
- [ ] Muestra impresa de 10 estudiantes con nombres, carreras y valores plausibles (revisión humana).

## Hito 2 — Modelo y explicaciones
**Lee:** `docs/DATA_MODEL.md` (§2, §5, §6, §7).
**Tareas**
- `ml/train.py`: partición estratificada 80/20 con semilla, XGBoost con `scale_pos_weight`, métricas F1/precisión/recall/PR-AUC en el conjunto de prueba, guardado de artefactos y registro en `model_versions`.
- `ml/explain.py`: SHAP `TreeExplainer`; `main_factor`, `top_factors` con las plantillas de texto.
- `services/rules.py`: razones de alerta por reglas.
- `services/scoring.py`: puntúa `student_features`, calibra umbrales por percentil (guardados en `model_versions`), escribe `risk_scores` y genera alertas según las reglas de `DATA_MODEL.md` §1. Actualiza la semana 8 de `weekly_snapshots`.
- `make train` ejecuta todo.

**Aceptación**
- [ ] `make train` imprime métricas y termina en < 2 min.
- [ ] Distribución Alto/Medio/Bajo ≈ 8/17/75% (±5 puntos) (test).
- [ ] Los 5 estudiantes curados reciben el nivel objetivo de `DATA_MODEL.md` §7 (test).
- [ ] Cada estudiante en Alto/Medio tiene exactamente 3 `top_factors` con texto legible y una alerta `pendiente`.
- [ ] El modelo **no** usa `gender` ni ninguna variable prohibida (test sobre la lista de features).
- [ ] Piso de cordura: F1 ≥ 0.55 en el conjunto de prueba (si falla, reportarlo; **no** manipular el generador).

## Hito 3 — API con roles
**Lee:** `docs/API_CONTRACT.md` (todo), `docs/PRD.md` §3.
**Tareas**
- JWT, dependencias `require_role("director")` / `require_role("tutor")`, verificación de propiedad del estudiante.
- Routers: `auth`, `dashboard`, `students`, `interventions`, `model` (el de `upload` queda para el hito 6).
- Registro de intervención con la lógica de alertas.

**Aceptación**
- [ ] Todos los endpoints de `API_CONTRACT.md` (salvo `upload`) responden con el esquema exacto, visibles en `/docs`.
- [ ] **Tests de acceso:** tutor sin token → 401; tutor llamando `/dashboard/summary` → 403; director llamando `/students` → 403; **Tutor 1 pidiendo un estudiante de Tutor 2 → 403** (detalle e intervenciones, lectura y escritura).
- [ ] `POST /students/{id}/interventions` con una reunión en el pasado → 422; con datos válidos → 201 y la alerta pasa a `atendida`; `critical_pending` baja en 1 si era Alto.
- [ ] `GET /students?risk=alto&q=mendoza` filtra correctamente e ignora tildes.
- [ ] `make gen-types` regenera los tipos sin errores.

## Hito 4 — Dashboard Ejecutivo
**Lee:** `docs/PRD.md` §4.1–4.2, `docs/mockups/`.
**Tareas**
- Login (guarda el token, redirige según rol), layout con sidebar por rol, rutas protegidas.
- Pantalla `/dashboard`: 4 KPIs, gráfico de tendencia (Recharts), barras apiladas por facultad, filtro de facultad, estados de carga y error.

**Aceptación**
- [ ] Login como Directivo → `/dashboard` con datos reales de la API; un tutor que abre `/dashboard` es redirigido.
- [ ] Cambiar el filtro de facultad actualiza KPIs y barras.
- [ ] Comparación visual con el mockup: misma estructura (4 KPIs arriba, dos gráficos abajo), colores de riesgo con icono y texto.
- [ ] Skeletons mientras carga y mensaje con "Reintentar" si la API falla.

## Hito 5 — Módulo Tutor y detalle
**Lee:** `docs/PRD.md` §4.5–4.7, `docs/mockups/`.
**Tareas**
- `/students` con banner de resumen, tabla, filtro por riesgo, buscador y acciones.
- `/students/:id` con aviso fijo, factores, indicadores e historial.
- Diálogo "Registrar intervención" con validación; pantalla "Sin acceso" ante 403.

**Aceptación**
- [ ] Como Tutor 1 se ven los 5 estudiantes curados (entre otros) con nivel, factor principal y razones.
- [ ] El filtro por riesgo y el buscador funcionan.
- [ ] Registrar un seguimiento persiste tras recargar, se ve en el historial y baja el contador de alertas críticas (si aplica).
- [ ] El aviso "señal de acompañamiento, no etiqueta" aparece en el detalle sin interacción previa.
- [ ] Abrir `/students/<id de Tutor 2>` muestra "No tienes acceso a este estudiante".

## Hito 6 — Carga de CSV y panel de modelo
**Lee:** `docs/DATA_MODEL.md` (§9, §1 reglas de alertas), `docs/API_CONTRACT.md` §3–4, `docs/PRD.md` §4.3–4.4.
**Tareas**
- `services/pipeline.py`: ingesta → validación → seudonimización → puntuación → alertas; registra `pipeline_runs`.
- `POST /api/upload`, `GET /api/upload/template.csv`, `make demo-csv`.
- Pantallas `/upload` (zona de carga, pipeline por pasos, errores, antes/después, "lo que ve el modelo") y `/model`.

**Aceptación**
- [ ] Ejecutar `make demo-csv` y subir `data/demo_upload.csv` desde la UI: muestra 5 pasos con conteos, 3 filas rechazadas en la tabla de errores y distribución antes → después con más riesgo Alto.
- [ ] Tras la carga, `/dashboard` refleja nuevos KPIs; **Diego Torres Ruiz** pasa a Alto y aparece con alerta pendiente para Tutor 1.
- [ ] Test del pipeline: archivo con filas inválidas procesa las válidas; un estudiante que mejora cierra su alerta; un estudiante nuevo se crea con `pseudo_id`.
- [ ] El bloque "Lo que ve el modelo" no muestra nombre ni código.
- [ ] `/model` muestra métricas y la etiqueta de datos sintéticos.

## Hito 7 — Pulido y demo
**Lee:** `docs/PRD.md` §5–6.
**Tareas**
- Estados vacíos, textos en español revisados, atajos de teclado y foco visibles, 404 amigable.
- Test e2e Playwright que recorre el guion de demo (login director → carga CSV → login tutor → registrar seguimiento → acceso denegado).
- `docs/ARCHITECTURE.md` breve (diagrama en texto, flujo de datos, decisiones, cómo cambiar `NOISE_SD`).
- `README.md` final con el guion de 5 minutos.

**Aceptación**
- [ ] `make setup && make seed && make train && make dev` y el guion completo corre sin errores, 3 veces seguidas (con `make seed && make train` entre corridas).
- [ ] `make e2e` pasa.
- [ ] Cada pantalla carga en < 2 s con 1,500 estudiantes.
- [ ] Revisión final contra la lista "Fuera de alcance" de `AGENTS.md`: nada de eso apareció.

---

## Definición de "terminado" (todos los hitos)
1. Criterios del hito verificados uno por uno (el agente lista cada uno con su evidencia).
2. `make test` en verde.
3. Sin dependencias nuevas sin justificar; sin código muerto ni TODOs sin explicar.
4. Commit pequeño y descriptivo.

## Si algo sale mal
- El agente se enreda o improvisa: `git reset --hard` al último commit bueno, reduce la tarea a una sola cosa y repite.
- Un documento resulta ambiguo: corrige el documento primero y luego pide la implementación; así el siguiente hito hereda la corrección.
