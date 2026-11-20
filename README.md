# EduPredict Demo

Prototipo de demostración de una plataforma que predice riesgo de deserción estudiantil y genera alertas para tutores. Todos los datos son sintéticos.

## Requisitos

- Python 3.12 (el `Makefile` lo instala vía `uv`)
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+

## Comandos

```bash
make setup       # instala backend y frontend, y genera los tipos
make seed        # crea la BD y genera los datos sintéticos
make train       # entrena el modelo y puntúa a los estudiantes
make dev         # API en :8000 y frontend en :5173
make test        # pytest + typecheck + build
make e2e         # pendiente — Hito 7
make gen-types   # regenera frontend/src/api/schema.d.ts desde OpenAPI
make demo-csv    # pendiente — Hito 6
```

## Desarrollo

```bash
make setup
make dev
```

Abre http://localhost:5173. El frontend hace proxy de `/api` hacia http://localhost:8000.

Documentación del producto en `docs/`.
