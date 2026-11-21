# Arquitectura — EduPredict Demo

Prototipo de demostración. Todos los datos son sintéticos; no hay integraciones reales ni
procesamiento de datos personales de estudiantes reales.

## Vista general

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Navegador                                                                │
│  React + Vite + TypeScript + Tailwind + Recharts + TanStack Query        │
│  http://localhost:5173                                                   │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ /api (proxy Vite)         JWT Bearer
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ API FastAPI — http://localhost:8000                                       │
│  routers/: auth · dashboard · students · interventions · upload · model   │
│  deps/: require_role(director|tutor) · ownership check                   │
└───────┬───────────────────────────────┬──────────────────────────────────┘
        │ SQLModel                      │ pickle/JSON
        ▼                               ▼
┌───────────────────────────┐   ┌──────────────────────────────────────────┐
│ SQLite                    │   │ Artefactos ML                            │
│ backend/data/edupredict.db│   │ backend/ml/artifacts/                    │
│                           │   │  xgb_model.json · metrics.json           │
│ students (identidad)      │   │  feature_columns.json                    │
│ student_features (pseudo) │   └──────────────────────────────────────────┘
│ historical_cohort         │
│ risk_scores · alerts      │
│ interventions · runs      │
└───────────────────────────┘
```

## Flujo de datos

1. **Semilla (`make seed`)** — `ml/generate_data.py` reinicia la BD y genera facultades,
   carreras, tutores, usuarios demo, 1,500 estudiantes, sus `student_features`
   seudonimizadas y 4,000 filas de `historical_cohort`. La identidad (`students`) y las
   features (`student_features`) se unen solo por `pseudo_id`.
2. **Entrenamiento (`make train`)** — `ml/train.py` entrena XGBoost sobre
   `historical_cohort` (80/20 estratificado, semilla fija), guarda el modelo y las métricas,
   y crea una fila activa en `model_versions`. Después `services/scoring.py` puntúa a todos
   los estudiantes, escribe `risk_scores` y abre/cierra alertas según las reglas.
3. **Consulta** — el frontend pide `/api/*` con el JWT del usuario. La API aplica rol y
   propiedad: el director recibe agregados; el tutor solo sus estudiantes. La identidad se
   resuelve en la API al responder, nunca dentro del modelo.
4. **Carga (`/upload`)** — `services/pipeline.py` recibe el CSV, valida filas, seudonimiza
   identificadores, actualiza `student_features`, vuelve a puntuar con los umbrales del
   modelo activo y registra `pipeline_runs` con pasos y distribución antes/después. Las filas
   inválidas se rechazan sin abortar el resto.

## Decisiones

- **Un solo modelo XGBoost** con `scale_pos_weight`; umbrales de nivel calibrados por
  percentil y guardados en `model_versions` para que la carga use los mismos cortes.
- **Seudonimización por HMAC-SHA256** (`PSEUDO_SECRET`) truncado a 16 hex. Es determinista,
  permite actualizar features de un estudiante sin conocer su identidad y evita filtrar
  nombres/códigos al modelo.
- **Sin fuga de datos:** `gender` se guarda pero no es feature; tampoco se usan solicitud de
  retiro ni señales de abandono. La lista de features se valida en tests.
- **Autorización en la API**, no solo en la UI. Los tests cubren 401/403 y el acceso cruzado
  entre tutores.
- **Tipos del frontend generados** desde OpenAPI (`make gen-types`); no se escriben a mano.
- **SQLite + SQLModel** por simplicidad de demo; sin migraciones ni multitenancy.
- **Sin acciones automáticas:** una alerta es una señal para acompañamiento humano. La UI
  muestra el aviso correspondiente en las vistas individuales.

## Cómo cambiar el ruido del generador

`backend/ml/generate_data.py` define `NOISE_SD = 0.7`, la desviación estándar del ruido que
se suma al logit de deserción de la cohorte histórica. Un valor mayor hace la etiqueta menos
predecible (métricas más bajas); uno menor la hace más separable (métricas más altas).

1. Edita `NOISE_SD` (mantén el resto de constantes y `SEED`).
2. Ejecuta `make seed && make train`.
3. Revisa las métricas en `/model` o en `backend/ml/artifacts/metrics.json`.

No ajustes el generador para alcanzar una cifra objetivo: la demo reporta las métricas tal
como salen.
