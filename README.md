# EduPredict Demo

Prototipo de demostración de una plataforma que predice riesgo de deserción estudiantil y
genera alertas para tutores. Todos los datos son sintéticos.

## Requisitos

- Python 3.12 (el `Makefile` lo instala vía `uv`)
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Para `make e2e`: Chromium del sistema en `/usr/bin/chromium` (o define
  `PLAYWRIGHT_CHROMIUM_PATH`).

## Puesta en marcha

```bash
make setup       # instala backend y frontend, y genera los tipos
make seed        # crea la BD y genera los datos sintéticos
make train       # entrena el modelo y puntúa a los estudiantes
make dev         # API en :8000 y frontend en :5173
```

Abre http://localhost:5173. El frontend hace proxy de `/api` hacia http://localhost:8000.
Documentación de la API en http://localhost:8000/docs.

## Configuración

Variables de entorno opcionales (los valores de desarrollo están en
`backend/app/config.py`):

| Variable | Uso |
|---|---|
| `JWT_SECRET` | Firma de los tokens de sesión. |
| `PSEUDO_SECRET` | HMAC para calcular `pseudo_id`; cambiarlo invalida los seudónimos existentes. |
| `PLAYWRIGHT_CHROMIUM_PATH` | Ruta al ejecutable de Chromium para `make e2e` (por defecto `/usr/bin/chromium`). |

La BD vive en `backend/data/edupredict.db` y los artefactos del modelo en
`backend/ml/artifacts/`; ambos están ignorados por git y se regeneran con `make seed` y
`make train`.

## Comandos

```bash
make setup       # instala dependencias de backend y frontend
make seed        # crea BD, genera datos sintéticos y usuarios demo (reinicia la BD)
make train       # entrena el modelo, guarda artefactos y puntúa a todos los estudiantes
make dev         # levanta API (8000) y frontend (5173)
make test        # pytest + typecheck del frontend + build del frontend
make e2e         # test de humo con Playwright (requiere seed + train)
make gen-types   # regenera frontend/src/api/schema.d.ts desde el OpenAPI
make demo-csv    # genera backend/data/demo_upload.csv para la demo de carga
```

## Guion de demo (5 minutos)

Usuarios demo (contraseña `demo1234`):

| Rol | Correo |
|---|---|
| Directivo | `director@edupredict.demo` |
| Tutor 1 — Prof. Roberto Díaz | `tutor1@edupredict.demo` |
| Tutor 2 — Prof. Mariela Salazar | `tutor2@edupredict.demo` |

Antes de empezar, deja el entorno limpio:

```bash
make seed && make train && make demo-csv
```

1. **Dashboard (60 s).** Entra como Directivo. Recorre los 4 KPIs, la tendencia de 8 semanas
   y la distribución por facultad. Cambia el filtro de facultad para mostrar que los
   indicadores se recalculan.
2. **Carga de datos (90 s).** Ve a **Carga de datos**, sube `backend/data/demo_upload.csv`
   y procesa. Muestra los 5 pasos del pipeline, las 3 filas rechazadas y la distribución
   antes → después con más riesgo Alto.
3. **Impacto en el dashboard (30 s).** Vuelve al dashboard: la matrícula y las alertas
   reflejan la carga.
4. **Tutor (90 s).** Cierra sesión y entra como Tutor 1. Busca "Diego Torres" (o pulsa `/`
   para enfocar el buscador): aparece en riesgo **Alto** con su factor principal y razones.
   Abre su ficha, lee el aviso de que la alerta es una señal de acompañamiento y registra un
   seguimiento. El historial se actualiza y el contador de alertas críticas baja.
5. **Privacidad y modelo (60 s).** Intenta abrir la ficha de un estudiante de Tutor 2: la API
   responde 403 y la UI muestra "No tienes acceso a este estudiante". Entra como Directivo y
   abre **Modelo** para ver métricas, importancia de variables y la etiqueta de datos
   sintéticos.

Para repetir la demo desde cero: `make seed && make train && make demo-csv`.

## Verificación

```bash
make test   # backend + frontend
make e2e    # guion automatizado con Playwright
```

`make e2e` reutiliza los servidores si ya están corriendo; si no, los levanta. Requiere una
BD sembrada y un modelo entrenado (`make seed && make train`).

## Despliegue en Render (plan free)

El repo incluye `Dockerfile` y `render.yaml`. La imagen compila el frontend, instala el
backend y genera los datos y entrena el modelo durante el build, así el servicio arranca con
datos y modelo listos.

1. Sube el repo a GitHub (ya está en `origin`).
2. En Render: **New → Blueprint**, selecciona el repo y aplica `render.yaml`.
   Alternativa: **New → Web Service → Docker** apuntando al repo.
3. Render asigna una URL `https://<servicio>.onrender.com`. El health check es `/api/meta`.

Notas del plan free:

- El servicio se duerme tras 15 minutos sin tráfico y tarda ~1 minuto en despertar.
- El filesystem es efímero: las cargas CSV y los seguimientos registrados se pierden al
  reiniciar o dormir. La demo vuelve al estado del build.
- `PSEUDO_SECRET` se deja con el valor de desarrollo para que el build y el runtime generen
  los mismos seudónimos. No uses datos reales ni este despliegue como producción.

Para probar la imagen localmente:

```bash
docker build -t edupredict-demo .
docker run --rm -p 8000:8000 -e JWT_SECRET=dev-jwt-secret-change-me-32-bytes-min edupredict-demo
```

Abre http://localhost:8000 (la API y el frontend se sirven desde el mismo puerto).

## Documentación

- `docs/ARCHITECTURE.md` — diagrama, flujo de datos y decisiones.
- `docs/PRD.md` — alcance y criterios de producto.
- `docs/DATA_MODEL.md` — tablas, variables y generador sintético.
- `docs/API_CONTRACT.md` — contrato de la API.
- `docs/MILESTONES.md` — hitos y criterios de aceptación.
