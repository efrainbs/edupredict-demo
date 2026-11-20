# EduPredict Demo — Reglas permanentes para el agente

## Qué es esto
Prototipo **de demostración** (side project) de una plataforma SaaS que predice riesgo de deserción estudiantil y genera alertas para tutores. Todos los datos son **sintéticos**. No es un producto: prioriza que la demo funcione y se vea bien sobre la completitud técnica.

## Antes de escribir código
1. Lee `docs/MILESTONES.md` y localiza el hito que te pidieron. **Implementa solo ese hito.**
2. Lee solo los documentos que ese hito cite (`docs/PRD.md`, `docs/DATA_MODEL.md`, `docs/API_CONTRACT.md`). No adivines lo que está documentado ahí; si algo es ambiguo o contradictorio, **pregunta** antes de improvisar.
3. Las referencias visuales están en `docs/mockups/`. Compara tu UI contra ellas antes de dar un hito por terminado.

## Stack fijo (no cambiar sin preguntar)
- **Backend:** Python 3.11 o 3.12, FastAPI, SQLModel, SQLite (archivo `backend/data/edupredict.db`), PyJWT, `bcrypt` (usar directamente, **no** passlib).
- **ML:** pandas, scikit-learn, XGBoost, SHAP (`TreeExplainer`). Un solo modelo: XGBoost.
- **Frontend:** React + Vite + TypeScript + Tailwind + shadcn/ui + Recharts + React Router + TanStack Query.
- **Tests:** pytest (backend), Playwright (un test de humo e2e).
- **Contrato:** los tipos TypeScript se **generan** desde el OpenAPI (`openapi-typescript`). No los escribas a mano.
- Puertos: API `8000`, frontend `5173` (Vite hace proxy de `/api` a `8000`).
- No agregues dependencias nuevas sin justificarlo en una línea al usuario.

## Comandos (el único vocabulario que debes usar)
```
make setup       # instala dependencias de backend y frontend
make seed        # crea BD, genera datos sintéticos y usuarios demo (reinicia la BD)
make train       # entrena el modelo, guarda artefactos y puntúa a todos los estudiantes
make dev         # levanta API (8000) y frontend (5173)
make test        # pytest + typecheck del frontend + build del frontend
make e2e         # test de humo con Playwright
make gen-types   # regenera frontend/src/api/schema.d.ts desde el OpenAPI
make demo-csv    # genera data/demo_upload.csv para la demo de carga
```
**Regla de cierre:** un hito no está terminado si `make test` falla. Al terminar, ejecuta `make test` y resume qué hiciste, qué verificaste y qué quedó pendiente.

## Reglas de dominio (innegociables)
- La alerta es una **señal de acompañamiento, no una etiqueta ni una sanción**. Toda vista de riesgo individual muestra este aviso. Ninguna acción automática afecta al estudiante.
- **Seudonimización:** el modelo y la tabla `student_features` **nunca** contienen nombre, código ni DNI. Solo `pseudo_id`. La unión con la identidad ocurre únicamente en la API al responder a un usuario autorizado.
- **Control de acceso:** el Tutor solo accede a **sus** estudiantes; el Directivo solo ve **agregados** (nunca lista individual). Se aplica en la API, no solo en la UI. Hay tests para esto.
- **Sin fuga de datos (leakage):** "solicitud de retiro", "retiro", "abandono" o cualquier variable que contenga el desenlace **no** puede ser feature del modelo.
- **Atributos sensibles:** `gender` se guarda pero **no** es feature del modelo.
- **Honestidad de la demo:** la UI muestra siempre un banner "Datos de demostración (sintéticos)". Las métricas del modelo se muestran tal como salen; **no ajustes el generador para alcanzar una cifra objetivo** (p. ej. F1 ≥ 85%).

## Fuera de alcance (no construir)
Conectores reales (Moodle/Canvas/ERP), pagos, facturación, soporte, multitenancy, "Pregunta a Gemini", reportes históricos, configuración de modelo editable, reentrenamiento desde la UI, notificaciones reales (correo/SMS). Si el menú del mockup los muestra, se **omiten**.

## Convenciones
- Código, nombres de variables, commits y comentarios en **inglés**. **Textos de la UI en español** (Perú).
- Estructura del repo:
  ```
  backend/app/{main,config,db,models,schemas,security,deps}.py
  backend/app/routers/{auth,dashboard,students,interventions,upload,model,meta}.py
  backend/app/services/{pseudonymize,scoring,pipeline,rules}.py
  backend/ml/{generate_data,features,train,explain}.py   (artefactos en backend/ml/artifacts/)
  backend/tests/
  frontend/src/{api,components,pages,lib}/
  frontend/e2e/
  ```
- Componentes pequeños, sin lógica de negocio en componentes de UI. Datos del servidor con TanStack Query.
- Secretos por variables de entorno con valores de desarrollo por defecto en `backend/app/config.py` (`JWT_SECRET`, `PSEUDO_SECRET`). Nunca commitear `.env`.
- Commits pequeños, uno por tarea lógica, mensaje en imperativo (`Add student detail endpoint`).
- Si te enredas: detente, resume el problema y pide al usuario revertir con git en lugar de apilar parches.
