# API_CONTRACT — Endpoints y respuestas

Base: `/api`. JSON salvo donde se indique. Autenticación: `Authorization: Bearer <JWT>` (PyJWT, HS256, expira en 8 h). Errores con forma `{"detail": "mensaje"}`.

Códigos comunes: `401` sin token o token inválido · `403` rol o recurso no permitido · `404` no existe · `422` validación.

El OpenAPI de FastAPI es la fuente de verdad de los tipos: cada endpoint usa `response_model` con un esquema Pydantic (`schemas.py`). Los nombres de campo de este documento son obligatorios; los ejemplos son ilustrativos.

## Resumen de permisos
| Endpoint | director | tutor |
|---|---|---|
| `POST /auth/login`, `GET /meta` | público | público |
| `GET /auth/me` | ✔ | ✔ |
| `GET /faculties`, `GET /dashboard/*` | ✔ | 403 |
| `POST /upload`, `GET /upload/template.csv`, `GET /model/info` | ✔ | 403 |
| `GET /tutor/summary`, `GET /students`, `GET /students/{id}`, `GET/POST /students/{id}/interventions` | 403 | ✔ (solo sus estudiantes) |

## 1. Auth y meta

### `POST /auth/login`
Body: `{"email": "tutor1@edupredict.demo", "password": "demo1234"}`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {"id": 2, "name": "Prof. Roberto Díaz", "role": "tutor", "tutor_id": 1}
}
```
`401` si las credenciales son incorrectas.

### `GET /auth/me` → `{"id", "name", "role", "tutor_id"}`

### `GET /meta`
```json
{"demo_mode": true,
 "banner": "Datos de demostración (sintéticos) — no representan estudiantes reales",
 "institution": "Instituto Superior Andino (demo)",
 "period": "2026-2"}
```

## 2. Dashboard (solo director)
Todos aceptan `?faculty_id=<int>` opcional (sin él = todas).

### `GET /faculties` → `[{"id": 1, "name": "Ingeniería"}, ...]`

### `GET /dashboard/summary`
```json
{
  "enrollment": 1500,
  "retention_rate": 0.842,
  "at_risk": {"count": 375, "pct": 0.25, "high": 120, "medium": 255},
  "alerts": {"pending": 310, "critical": 96}
}
```
`retention_rate` = 1 − (tasa de deserción de `historical_cohort`), constante; con filtro de facultad puede usarse el mismo valor global.

### `GET /dashboard/trend`
```json
{"weeks": [
  {"week": 1, "real_dropout_pct": 2.1, "projected_risk_pct": 18.0},
  ...
  {"week": 8, "real_dropout_pct": 7.9, "projected_risk_pct": 25.0}
]}
```
Con `faculty_id` se admite devolver la misma serie global (documentado en la UI como "serie institucional").

### `GET /dashboard/risk-by-faculty`
```json
{"faculties": [
  {"faculty_id": 1, "name": "Ingeniería", "high": 40, "medium": 85, "low": 400},
  ...
]}
```

## 3. Carga de datos (solo director)

### `GET /upload/template.csv`
Respuesta `text/csv` con la cabecera y 2 filas de ejemplo (columnas en `DATA_MODEL.md` §9).

### `POST /upload`
`multipart/form-data` con campo `file` (CSV, UTF-8, máx. 5 MB). `422` si no es CSV o faltan columnas obligatorias de cabecera.
```json
{
  "run_id": 7,
  "steps": [
    {"key": "ingest", "label": "Ingesta", "detail": "200 filas recibidas"},
    {"key": "clean", "label": "Limpieza y validación", "detail": "197 válidas, 3 rechazadas"},
    {"key": "pseudonymize", "label": "Seudonimización", "detail": "197 identificadores reemplazados por seudónimos"},
    {"key": "score", "label": "Puntuación", "detail": "197 estudiantes puntuados con modelo v1"},
    {"key": "alerts", "label": "Alertas", "detail": "58 nuevas, 11 cerradas"}
  ],
  "errors": [{"row": 14, "column": "tasa_asistencia", "reason": "Valor fuera de rango (1.4)"}],
  "distribution_before": {"high": 120, "medium": 255, "low": 1125},
  "distribution_after": {"high": 158, "medium": 270, "low": 1087},
  "model_view_sample": [
    {"pseudo_id": "a3f9c21b7d04e855", "gpa_avg": 9.8, "attendance_rate": 0.62, "tuition_debt_months": 2, "...": "..."}
  ]
}
```
`model_view_sample` = 3 filas de `student_features` (sin nombre ni código). Procesa filas válidas aunque otras fallen. Es síncrono (debe responder en < 10 s con 200 filas).

## 4. Modelo (solo director)

### `GET /model/info`
```json
{
  "algorithm": "XGBoost",
  "trained_at": "2026-11-19T14:02:11Z",
  "n_train": 4000,
  "metrics": {"f1": 0.74, "precision": 0.71, "recall": 0.78, "pr_auc": 0.80},
  "data_source": "synthetic",
  "disclaimer": "Métricas sobre datos sintéticos — no son evidencia de desempeño real",
  "feature_importance": [{"feature": "tuition_debt_months", "label": "Deuda de pensión (meses)", "importance": 0.19}]
}
```
`feature_importance`: top 10, etiquetas de `DATA_MODEL.md` §2.

## 5. Tutor (solo tutor)

### `GET /tutor/summary`
```json
{"tutor_name": "Prof. Roberto Díaz", "in_observation": 14, "critical_pending": 3}
```
`in_observation` = estudiantes propios con nivel alto o medio. `critical_pending` = alertas `pendiente` con nivel alto de sus estudiantes.

### `GET /students`
Query opcional: `risk=alto|medio|bajo`, `q=<texto>` (busca en nombre o código, sin distinguir tildes ni mayúsculas). Sin paginación (≤ 100 por tutor). Orden: nivel (alto→medio→bajo), luego `probability` desc.
```json
[{
  "id": 101,
  "code": "U00234512",
  "full_name": "Carlos Mendoza Ríos",
  "career": "Ing. de Software",
  "cycle": 4,
  "risk_level": "alto",
  "probability": 0.81,
  "main_factor": "Bajo rendimiento",
  "reasons": ["3 inasistencias consecutivas", "Nota de parcial: 08/20"],
  "pending_alerts": 1,
  "last_contact_at": "2026-11-17T15:30:00Z"
}]
```
`last_contact_at` = fecha de la última intervención o `null` ("Sin contacto").

### `GET /students/{id}`
`403` si el estudiante no es del tutor autenticado; `404` si no existe.
```json
{
  "id": 101, "code": "U00234512", "full_name": "Carlos Mendoza Ríos",
  "career": "Ing. de Software", "faculty": "Ingeniería", "cycle": 4,
  "risk": {
    "level": "alto", "probability": 0.81, "score": 81,
    "main_factor": "Bajo rendimiento", "computed_at": "2026-11-19T14:05:00Z",
    "top_factors": [
      {"feature": "attendance_rate", "group": "Asistencia", "impact": 0.42, "text": "Asistencia de 62%"},
      {"feature": "last_exam_grade", "group": "Rendimiento", "impact": 0.31, "text": "Nota de último parcial: 8.0/20"},
      {"feature": "lms_participation", "group": "Participación LMS", "impact": 0.18, "text": "Baja participación en el LMS (22%)"}
    ],
    "disclaimer": "Esta alerta es una señal para ofrecer acompañamiento oportuno. No es una etiqueta definitiva ni genera ninguna sanción automática."
  },
  "indicators": {
    "gpa_avg": 9.8, "attendance_rate": 0.62, "lms_participation": 0.22,
    "tuition_debt_months": 0, "weekly_work_hours": 20,
    "family_support": 3, "socioemotional_adaptation": 3
  },
  "interventions": []
}
```
`interventions` = mismo formato que el punto siguiente, más reciente primero.

### `GET /students/{id}/interventions` → lista (mismos permisos que el detalle)
```json
[{"id": 12, "type": "reunion", "note": "Se acordó plan de tutorías.",
  "scheduled_at": "2026-11-25T10:00:00Z", "created_at": "2026-11-19T16:00:00Z",
  "tutor_name": "Prof. Roberto Díaz"}]
```

### `POST /students/{id}/interventions`
Body: `{"type": "seguimiento", "note": "Llamé al estudiante...", "scheduled_at": null}`
- `type` ∈ `seguimiento|reunion|mensaje`; `note` obligatoria (1–500 caracteres); `scheduled_at` solo válido y obligatorio si `type = reunion`, y debe ser futuro.
- `201` con la intervención creada. Efecto: las alertas `pendiente` del estudiante pasan a `atendida`.
- `403` si el estudiante es ajeno. `422` por validación. **No envía mensajes reales.**
