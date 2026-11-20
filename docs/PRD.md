# PRD — EduPredict Demo

## 1. Propósito
Demostrar de punta a punta la idea del documento "Programa de Predicción de Riesgo Académico (PA3)": **datos institucionales → ETL con seudonimización → modelo de riesgo → alertas → intervención del tutor**, con datos sintéticos y en una sola sesión de 5 minutos.

**Éxito de la demo =** alguien ve el flujo completo sin que nada falle, entiende por qué un estudiante está en riesgo y ve que el tutor solo accede a lo suyo.

## 2. Alcance

### Entra
1. Login con 3 usuarios demo (Directivo, Tutor 1, Tutor 2).
2. **Dashboard Ejecutivo** (Directivo): 4 KPIs, tendencia, riesgo por facultad, filtro por facultad.
3. **Carga de datos** (Directivo): subir CSV → pipeline visible por pasos → riesgos recalculados.
4. **Panel de modelo** (Directivo): métricas del modelo activo con etiqueta de datos sintéticos.
5. **Mis estudiantes** (Tutor): banner de resumen, lista filtrable por riesgo, buscador.
6. **Detalle de estudiante** (Tutor): riesgo, top 3 factores en lenguaje natural, indicadores, historial, aviso "señal, no etiqueta".
7. **Registrar intervención** (seguimiento, reunión, mensaje) que persiste y atiende la alerta.
8. Banner global "Datos de demostración (sintéticos)".

### No entra
Ver lista en `AGENTS.md` → "Fuera de alcance".

## 3. Roles
| Rol | Ve | No puede |
|---|---|---|
| **Directivo** (`director`) | Agregados institucionales, carga de datos, panel de modelo | Ver listas ni detalle de estudiantes individuales |
| **Tutor** (`tutor`) | Sus estudiantes asignados, sus alertas, historial de sus intervenciones | Ver estudiantes de otros tutores, ver el dashboard ejecutivo, subir datos |

Usuarios demo (contraseña para todos: `demo1234`):
- `director@edupredict.demo` — "Dirección Académica"
- `tutor1@edupredict.demo` — "Prof. Roberto Díaz"
- `tutor2@edupredict.demo` — "Prof. Mariela Salazar"

Institución ficticia: **Instituto Superior Andino (demo)**.

## 4. Pantallas
Referencias visuales: `docs/mockups/`. Replicar estructura y jerarquía, no píxel por píxel.

### 4.1 Layout general
- Sidebar izquierda con logo "EduPredict AI" y navegación **según rol**:
  - Directivo: Dashboard Ejecutivo · Carga de datos · Modelo.
  - Tutor: Mis estudiantes.
- Cabecera con título de la vista, usuario (avatar con iniciales + nombre + rol) y botón "Cerrar sesión".
- Banner fino superior, siempre visible: "Datos de demostración (sintéticos) — no representan estudiantes reales".
- Tokens: acento índigo (`indigo-600`), fondo `slate-50`, tarjetas blancas con borde `slate-200` y esquinas `rounded-xl`. Riesgo: **Alto** rojo (`red`), **Medio** ámbar (`amber`), **Bajo** verde (`emerald`), siempre con icono + texto (no solo color). Fuente: Inter o la del sistema.

### 4.2 Dashboard Ejecutivo (`/dashboard`)
- Filtro de facultad (opciones: "Todas las facultades" + 4 facultades). El periodo se muestra fijo: `2026-2`.
- 4 tarjetas KPI:
  - **Matrícula total** (nº de estudiantes activos).
  - **Tasa de retención global** (% con barra de progreso).
  - **Estudiantes en riesgo** (nº Alto+Medio y % del total).
  - **Alertas pendientes** (nº y subtítulo "N críticas").
- **Tendencia de deserción y riesgo**: líneas de 8 semanas, series "% Deserción real" y "% Riesgo proyectado", tooltip al pasar el cursor.
- **Distribución de niveles de riesgo por facultad**: barras apiladas (Alto/Medio/Bajo) por facultad.
- Estados: cargando (skeletons), error (mensaje + reintentar).

### 4.3 Carga de datos (`/upload`)
- Zona para arrastrar/seleccionar CSV y enlace "Descargar plantilla".
- Tras subir: **pipeline por pasos** con conteos —
  `1 Ingesta (filas recibidas) → 2 Limpieza (válidas / rechazadas) → 3 Seudonimización (identificadores reemplazados) → 4 Puntuación (estudiantes puntuados) → 5 Alertas (nuevas / cerradas)`.
- Tabla de errores de validación (fila, columna, motivo) si los hay.
- Comparación "antes → después" de la distribución de riesgo (Alto/Medio/Bajo).
- Un bloque "Lo que ve el modelo" con 3 filas de ejemplo ya seudonimizadas (sin nombre ni código), para mostrar el concepto.

### 4.4 Panel de modelo (`/model`)
Tarjeta con: algoritmo, fecha de entrenamiento, nº de registros de entrenamiento, F1, precisión, recall, PR-AUC, y la etiqueta **"Métricas sobre datos sintéticos — no son evidencia de desempeño real"**. Gráfico de barras con importancia global de variables (top 10).

### 4.5 Mis estudiantes (`/students`)
- Banner índigo: "¡Hola, {nombre}! Tienes **N** estudiantes en observación" (N = Alto+Medio) y a la derecha "Alertas críticas: **M** sin atender" (Alto con alerta pendiente).
- Tabla: Estudiante/Carrera · Nivel de riesgo · Factor principal · Alertas (razones) · Último contacto · Acciones (**Seguimiento**, **Agendar**, **Mensaje**).
- Filtro por riesgo (Todos/Alto/Medio/Bajo) y buscador por nombre o código. Orden: Alto → Medio → Bajo, luego probabilidad descendente.
- Las acciones abren un diálogo para registrar la intervención (ver 4.6).
- Click en la fila → detalle.

### 4.6 Detalle de estudiante (`/students/:id`)
- Cabecera: nombre, código, carrera, ciclo, badge de riesgo y probabilidad (como "Puntaje de riesgo: 78/100").
- **Aviso fijo y visible:** "Esta alerta es una señal para ofrecer acompañamiento oportuno. No es una etiqueta definitiva ni genera ninguna sanción automática."
- **Por qué aparece esta alerta:** top 3 factores con texto legible (ver `DATA_MODEL.md` §6) e indicador de dirección.
- **Indicadores actuales:** promedio, asistencia, participación LMS, deuda, horas de trabajo, apoyo familiar, adaptación.
- **Historial de intervenciones** (más reciente primero) y botón "Registrar intervención".
- Si un tutor abre un estudiante ajeno: pantalla "No tienes acceso a este estudiante" (la API responde 403).

### 4.7 Diálogo "Registrar intervención"
Campos: tipo (Seguimiento / Reunión / Mensaje), nota (obligatoria, máx. 500 caracteres), fecha (solo para Reunión). Al guardar: se agrega al historial, la alerta pendiente del estudiante pasa a "atendida", el contador de "alertas críticas sin atender" se actualiza y se muestra una confirmación. **No se envía ningún mensaje real.**

## 5. Guion de demo (5 minutos)
| Min | Acción | Qué debe verse |
|---|---|---|
| 0:00 | Login como Directivo | Dashboard con KPIs, tendencia y barras por facultad. Filtrar por "Ingeniería" y volver a "Todas". |
| 1:15 | Ir a **Carga de datos**, subir `data/demo_upload.csv` | Pipeline por pasos con conteos; comparación antes/después; las alertas pendientes suben. Volver al dashboard: los KPIs cambiaron. |
| 2:30 | Cerrar sesión, login como Tutor 1 | Banner con estudiantes en observación y alertas críticas. **Diego Torres Ruiz** (antes Bajo) ahora aparece en riesgo Alto tras la carga. |
| 3:15 | Abrir un estudiante en riesgo Alto, registrar un seguimiento | Factores explicados, aviso "señal, no etiqueta"; la alerta pasa a atendida y el contador baja. |
| 4:15 | Con Tutor 1, abrir manualmente la URL de un estudiante de Tutor 2 | "No tienes acceso a este estudiante" (control de acceso). |
| 4:40 | Login Directivo → **Modelo** | Métricas con la etiqueta de datos sintéticos. Cierre. |

## 6. Requisitos no funcionales
- Cada pantalla carga en < 2 s con ~1,500 estudiantes.
- `make setup && make seed && make train && make dev` deja la demo lista, sin pasos manuales adicionales.
- Funciona en Chrome de escritorio (≥ 1280 px). Móvil no es requisito.
- Sin dependencias de servicios externos ni de internet durante la demo.
- Accesibilidad básica: contraste suficiente, riesgo indicado con texto además de color, controles operables con teclado.

## 7. Supuestos y decisiones abiertas
- Escala de notas vigesimal (0–20), como en el sistema peruano.
- "Retención global" es un indicador derivado de la cohorte histórica sintética, no medido en vivo.
- La carga de CSV **actualiza** a estudiantes existentes (por código) y crea los nuevos; no borra a quienes no vengan en el archivo.
- La demo corre en local. Un despliegue público queda fuera de este alcance inicial.
