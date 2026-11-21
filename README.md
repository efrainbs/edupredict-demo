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

## Documentación

- `docs/ARCHITECTURE.md` — diagrama, flujo de datos y decisiones.
- `docs/PRD.md` — alcance y criterios de producto.
- `docs/DATA_MODEL.md` — tablas, variables y generador sintético.
- `docs/API_CONTRACT.md` — contrato de la API.
- `docs/MILESTONES.md` — hitos y criterios de aceptación.
