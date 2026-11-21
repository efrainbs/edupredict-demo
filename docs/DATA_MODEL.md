# DATA_MODEL — Tablas, variables y generador sintético

BD: SQLite vía SQLModel. Campos JSON con `sa_column=Column(JSON)`. Fechas en UTC (ISO 8601).

## 1. Tablas

### Identidad y estructura (contienen datos identificables)
| Tabla | Campos |
|---|---|
| `users` | `id`, `email` (único), `name`, `role` (`director`\|`tutor`), `password_hash`, `tutor_id` (FK `tutors`, nulo para director) |
| `tutors` | `id`, `name` |
| `faculties` | `id`, `name` |
| `careers` | `id`, `name`, `faculty_id` |
| `students` | `id`, `code` (único, ej. `U00234512`), `full_name`, `gender` (`F`\|`M`), `career_id`, `cycle` (1–6), `tutor_id`, `pseudo_id` (único) |

### Sin identidad (lo único que ve el modelo)
| Tabla | Campos |
|---|---|
| `student_features` | `pseudo_id` (PK), las 17 variables de la sección 2, `updated_at` |
| `historical_cohort` | `id`, las 17 variables, `dropped_out` (0/1) — datos de entrenamiento, sin ninguna referencia a `students` |

### Resultados y operación
| Tabla | Campos |
|---|---|
| `model_versions` | `id`, `algorithm`, `trained_at`, `n_train`, `f1`, `precision`, `recall`, `pr_auc`, `threshold` (JSON: `{high, medium}`), `feature_importance` (JSON: lista `{feature, importance}`), `is_active`, `data_source` (siempre `"synthetic"`) |
| `risk_scores` | `student_id` (PK; solo el último puntaje), `probability` (0–1), `level` (`alto`\|`medio`\|`bajo`), `main_factor` (grupo o `"Ninguno"`), `top_factors` (JSON, ver §6), `model_version_id`, `computed_at` |
| `alerts` | `id`, `student_id`, `level`, `main_factor`, `reasons` (JSON lista de strings), `status` (`pendiente`\|`atendida`\|`cerrada`), `created_at`, `resolved_at` |
| `interventions` | `id`, `student_id`, `tutor_id`, `type` (`seguimiento`\|`reunion`\|`mensaje`), `note`, `scheduled_at` (nulo salvo reunión), `created_at` |
| `weekly_snapshots` | `week_index` (1–8), `real_dropout_pct`, `projected_risk_pct` |
| `pipeline_runs` | `id`, `started_at`, `source` (`seed`\|`upload`), `steps` (JSON, ver API §upload), `distribution_before`, `distribution_after` |

**Regla de seudonimización:** `pseudo_id = hex(HMAC_SHA256(PSEUDO_SECRET, student_code))[:16]`. Se calcula en `services/pseudonymize.py` y es la **única** función que une `students` con `student_features`.

**Reglas de alertas:**
- Al puntuar: si `level` ∈ {alto, medio} y el estudiante no tiene alerta `pendiente` → crear alerta `pendiente`.
- Si el nivel pasa a `bajo` → alertas pendientes del estudiante pasan a `cerrada`.
- Al registrar una intervención → alertas `pendiente` del estudiante pasan a `atendida` (`resolved_at` = ahora).
- "Alertas críticas sin atender" = alertas `pendiente` con `level = alto`.

## 2. Variables del modelo (17)

| Variable | Tipo / rango | Grupo | Etiqueta UI |
|---|---|---|---|
| `gpa_avg` | float 0–20 | Rendimiento | Promedio ponderado |
| `grade_trend` | float −5..+5 (variación vs. ciclo previo) | Rendimiento | Tendencia de notas |
| `last_exam_grade` | float 0–20 | Rendimiento | Nota del último parcial |
| `failed_courses` | int 0–6 | Rendimiento | Cursos desaprobados |
| `attendance_rate` | float 0–1 | Asistencia | Asistencia |
| `consecutive_absences` | int 0–10 | Asistencia | Inasistencias consecutivas |
| `lms_participation` | float 0–1 | Participación LMS | Participación en el LMS |
| `late_assignments_rate` | float 0–1 | Participación LMS | Entregas tardías |
| `tuition_debt_months` | int 0–4 | Económico / Laboral | Deuda de pensión (meses) |
| `scholarship` | 0/1 | Económico / Laboral | Beca |
| `weekly_work_hours` | int 0–48 | Económico / Laboral | Horas de trabajo semanales |
| `commute_minutes` | int 5–150 | Económico / Laboral | Tiempo de traslado |
| `family_support` | int 1–5 | Socioemocional | Apoyo familiar |
| `socioemotional_adaptation` | int 1–5 | Socioemocional | Adaptación socioemocional |
| `shift` | `diurno`/`nocturno` (one-hot) | Económico / Laboral | Turno nocturno |
| `cycle` | int 1–6 | Rendimiento | Ciclo |
| `age` | int 17–40 | Socioemocional | Edad |

**Excluidos de las variables** (nunca como feature): `gender`, nombre, código, `solicitud de retiro` o cualquier señal de abandono.

## 3. Generador sintético (`backend/ml/generate_data.py`)
Semilla fija (`SEED=42`) para reproducibilidad. Todo parámetro numérico va en constantes con nombre al inicio del archivo.

**Variables latentes por estudiante** (independientes, N(0,1)): `ability`, `engagement`, `stress` (estrés económico).

**Derivación (guía; ajustar rangos con `clip`):**
- `gpa_avg ≈ 13 + 2.2·ability + 0.8·engagement + N(0,0.8)`; `last_exam_grade ≈ gpa_avg + N(0,2)`; `grade_trend ≈ 0.8·(engagement + ability)/2 + N(0,1)`.
- `failed_courses ~ Poisson(max(0.3, 1.2 − 0.5·ability − 0.3·engagement))`, tope 6.
- `attendance_rate ≈ 0.85 + 0.07·engagement − 0.03·stress + N(0,0.05)`; `consecutive_absences ~ Poisson(max(0, 1 − 0.8·engagement + 0.3·stress))`, tope 10.
- `lms_participation ≈ 0.6 + 0.15·engagement + N(0,0.1)`; `late_assignments_rate ≈ 0.2 − 0.08·engagement + N(0,0.07)`.
- `tuition_debt_months`: 0 con prob. alta; sube con `stress` (usar umbrales sobre `stress + N(0,0.5)`).
- `weekly_work_hours ≈ max(0, 12 + 9·stress + N(0,6))`; 25% de estudiantes con valor 0; turno `nocturno` con prob. creciente en horas de trabajo.
- `scholarship`: prob. 25%, mayor con `ability` alta y `stress` alta.
- `commute_minutes ≈ 50 + 15·stress + N(0,20)`.
- `family_support` y `socioemotional_adaptation`: enteros 1–5 de `3 − 0.6·stress + 0.5·engagement + N(0,0.8)` redondeados.
- `cycle` uniforme 1–6; `age` ≈ 18–22 en diurno, 20–34 en nocturno.

**Etiqueta `dropped_out`** (solo para `historical_cohort`): `Bernoulli(sigmoid(z))` con

```
z = b0
  - 0.25*(gpa_avg - 13)      - 0.30*grade_trend       + 0.35*failed_courses
  - 3.0*(attendance_rate - 0.85)   + 0.25*max(consecutive_absences - 1, 0)
  - 1.5*(lms_participation - 0.6)  + 0.8*(late_assignments_rate - 0.2)
  + 0.55*tuition_debt_months       + 0.04*max(weekly_work_hours - 15, 0)
  + 0.008*max(commute_minutes - 45, 0)
  - 0.35*(family_support - 3)      - 0.40*(socioemotional_adaptation - 3)
  - 0.5*scholarship                + 0.30*(shift == nocturno)
  + N(0, NOISE_SD)
```
- `b0` se calibra por bisección para que la prevalencia sea **15–20%**.
- `NOISE_SD = 0.7` por defecto (constante visible). Con este valor se espera un F1 moderado (≈ 0.65–0.80). **No bajarlo para inflar el F1**; si se cambia, anotarlo en `ARCHITECTURE.md`.

## 4. Tamaños del seed
| Conjunto | Tamaño |
|---|---|
| `historical_cohort` | 4,000 filas |
| `students` (periodo actual 2026-2) | 1,500 |
| Tutores | 20 (2 con login). Cada tutor tiene 50–100 estudiantes |
| Facultades | 4: Ingeniería, Negocios, Salud, Artes y Diseño |
| Carreras | Ingeniería: Ing. de Software, Ing. Industrial · Negocios: Administración, Contabilidad · Salud: Enfermería, Farmacia · Artes y Diseño: Diseño Gráfico, Diseño de Interiores |

Reparto por facultad aproximado: Ingeniería 35%, Negocios 35%, Salud 18%, Artes y Diseño 12%.

Nombres: combinar nombres y apellidos peruanos comunes (ej. Carlos, Ana, Luis, Sofía, Diego, Valeria, Jorge, Camila / Mendoza, Quispe, Flores, Rojas, Huamán, Castro, Torres, Vega, Mamani, Ríos). Códigos `U` + 8 dígitos únicos.

**Distribución de riesgo esperada tras `make train`** (verificada por test, con tolerancia ±5 puntos): Alto ≈ 8%, Medio ≈ 17%, Bajo ≈ 75%.

## 5. Niveles de riesgo
Umbrales sobre `probability`, definidos en `config.py` y **calibrados en `make train`** como percentiles del conjunto de estudiantes actuales: `alto` = percentil ≥ 92 (≈ 8%), `medio` = percentil 75–92 (≈ 17%), `bajo` = resto. Se guardan los valores absolutos de corte en `model_versions` para reutilizarlos al re-puntuar en la carga de CSV (no recalibrar al subir).

## 6. Explicaciones (SHAP → lenguaje natural)

**Factor principal** (`main_factor`): suma de valores SHAP **positivos** (empujan hacia riesgo) por **grupo** (Rendimiento, Asistencia, Participación LMS, Económico / Laboral, Socioemocional); gana el grupo con mayor suma. Mapeo a etiquetas de la UI: Rendimiento → "Bajo rendimiento", Asistencia → "Inasistencias", Participación LMS → "Baja participación", Económico / Laboral → "Económico / Laboral", Socioemocional → "Socioemocional". Si `level = bajo` → `"Ninguno"`.

**Top 3 factores** (`top_factors`): las 3 variables con mayor SHAP positivo, como lista:
```json
{"feature": "tuition_debt_months", "group": "Económico / Laboral", "impact": 0.42,
 "text": "Deuda de pensión de 2 meses"}
```
Plantillas de `text` (según valor real de la variable):
| Variable | Plantilla |
|---|---|
| `tuition_debt_months` | "Deuda de pensión de {n} meses" |
| `weekly_work_hours` | "Trabaja {n} horas semanales" |
| `commute_minutes` | "Traslado de {n} minutos" |
| `gpa_avg` | "Promedio de {x}/20" |
| `grade_trend` | "Notas en descenso respecto al ciclo anterior" |
| `last_exam_grade` | "Nota de último parcial: {x}/20" |
| `failed_courses` | "{n} cursos desaprobados" |
| `attendance_rate` | "Asistencia de {p}%" |
| `consecutive_absences` | "{n} inasistencias consecutivas" |
| `lms_participation` | "Baja participación en el LMS ({p}%)" |
| `late_assignments_rate` | "{p}% de entregas tardías" |
| `family_support` | "Bajo apoyo familiar percibido" |
| `socioemotional_adaptation` | "Dificultades de adaptación socioemocional" |
| `scholarship` | "Sin beca" |
| `shift` | "Estudia en turno nocturno" |
| `cycle`, `age` | "Ciclo {n}" / "Edad {n}" |

**Razones de alerta** (`reasons`, mostradas en la columna "Alertas" de la lista): se generan con **reglas sobre valores crudos**, no con SHAP, en `services/rules.py`. Máximo 2 por estudiante, en este orden de prioridad:
1. `consecutive_absences ≥ 3` → "{n} inasistencias consecutivas"
2. `last_exam_grade ≤ 10` → "Nota de parcial: {x}/20"
3. `tuition_debt_months ≥ 2` → "Deuda pendiente ({n} meses)"
4. `lms_participation < 0.30` → "Baja participación en LMS"
5. `grade_trend ≤ -2` → "Pérdida de promedio"

## 7. Estudiantes curados (para que la demo se parezca al mockup)
El seed debe garantizar estos 5 estudiantes asignados a **Tutor 1** (Prof. Roberto Díaz). Se fijan sus variables manualmente (valores coherentes con el nivel), **antes** de puntuar, y el test del hito 2 verifica que el modelo les asigne el nivel indicado (si no, ajustar sus variables, nunca los umbrales):

| Nombre | Carrera | Nivel objetivo | Factor principal esperado |
|---|---|---|---|
| Carlos Mendoza Ríos | Ing. de Software | Alto | Bajo rendimiento |
| Ana López Silva | Administración | Alto | Económico / Laboral |
| Luis Quispe Mamani | Ing. Industrial | Medio | Inasistencias |
| Sofía Castro Vega | Enfermería | Medio | Socioemocional |
| Diego Torres Ruiz | Diseño Gráfico | **Bajo** (cambia a Alto con `demo_upload.csv`) | Ninguno |

## 8. `weekly_snapshots`
8 semanas. `real_dropout_pct`: sube suavemente de ~2 a ~8. `projected_risk_pct`: sube de ~18 a ~25, y la **semana 8 debe igualar el % de riesgo (Alto+Medio) actual calculado en vivo**. Cada ejecución de `make train` y cada carga de CSV actualiza la semana 8.

## 9. CSV de carga (`GET /api/upload/template.csv`)
Una fila por estudiante. Columnas (en este orden):
```
student_code,full_name,gender,career,cycle,tutor_name,
gpa_avg,grade_trend,last_exam_grade,failed_courses,attendance_rate,consecutive_absences,
lms_participation,late_assignments_rate,tuition_debt_months,scholarship,weekly_work_hours,
commute_minutes,family_support,socioemotional_adaptation,shift,age
```
Validaciones (fila rechazada con motivo si falla): código no vacío; `career` existente; `tutor_name` existente (tabla `tutors`) para estudiantes nuevos (para existentes se conserva el tutor); rangos de la tabla §2; `shift` ∈ {diurno, nocturno}; sin duplicados de código en el archivo. Filas válidas se procesan aunque otras se rechacen.

`make demo-csv` genera `backend/data/demo_upload.csv` con ~200 filas: ~120 estudiantes existentes con indicadores empeorados (más deuda, menos asistencia, menos LMS), **incluido Diego Torres Ruiz** (debe quedar en Alto), 60 existentes sin cambios, 15 estudiantes nuevos y **3 filas inválidas** a propósito (para mostrar la tabla de errores).
