from collections.abc import Sequence
from typing import Any

import pandas as pd

FEATURE_COLUMNS = [
    "gpa_avg",
    "grade_trend",
    "last_exam_grade",
    "failed_courses",
    "attendance_rate",
    "consecutive_absences",
    "lms_participation",
    "late_assignments_rate",
    "tuition_debt_months",
    "scholarship",
    "weekly_work_hours",
    "commute_minutes",
    "family_support",
    "socioemotional_adaptation",
    "shift",
    "cycle",
    "age",
]

INTEGER_FEATURES = {
    "failed_courses",
    "consecutive_absences",
    "tuition_debt_months",
    "scholarship",
    "weekly_work_hours",
    "commute_minutes",
    "family_support",
    "socioemotional_adaptation",
    "cycle",
    "age",
}

FEATURE_GROUPS = {
    "gpa_avg": "Rendimiento",
    "grade_trend": "Rendimiento",
    "last_exam_grade": "Rendimiento",
    "failed_courses": "Rendimiento",
    "attendance_rate": "Asistencia",
    "consecutive_absences": "Asistencia",
    "lms_participation": "Participación LMS",
    "late_assignments_rate": "Participación LMS",
    "tuition_debt_months": "Económico / Laboral",
    "scholarship": "Económico / Laboral",
    "weekly_work_hours": "Económico / Laboral",
    "commute_minutes": "Económico / Laboral",
    "family_support": "Socioemocional",
    "socioemotional_adaptation": "Socioemocional",
    "shift": "Económico / Laboral",
    "cycle": "Rendimiento",
    "age": "Socioemocional",
}

GROUP_LABELS = {
    "Rendimiento": "Bajo rendimiento",
    "Asistencia": "Inasistencias",
    "Participación LMS": "Baja participación",
    "Económico / Laboral": "Económico / Laboral",
    "Socioemocional": "Socioemocional",
}

FEATURE_LABELS = {
    "gpa_avg": "Promedio ponderado",
    "grade_trend": "Tendencia de notas",
    "last_exam_grade": "Nota del último parcial",
    "failed_courses": "Cursos desaprobados",
    "attendance_rate": "Asistencia",
    "consecutive_absences": "Inasistencias consecutivas",
    "lms_participation": "Participación en el LMS",
    "late_assignments_rate": "Entregas tardías",
    "tuition_debt_months": "Deuda de pensión (meses)",
    "scholarship": "Beca",
    "weekly_work_hours": "Horas de trabajo semanales",
    "commute_minutes": "Tiempo de traslado",
    "family_support": "Apoyo familiar",
    "socioemotional_adaptation": "Adaptación socioemocional",
    "shift": "Turno nocturno",
    "cycle": "Ciclo",
    "age": "Edad",
}


def feature_frame(rows: Sequence[Any]) -> pd.DataFrame:
    records = []
    for row in rows:
        record = {}
        for name in FEATURE_COLUMNS:
            value = getattr(row, name)
            if name == "shift":
                record[name] = 1 if value == "nocturno" else 0
            elif name in INTEGER_FEATURES:
                record[name] = int(value)
            else:
                record[name] = float(value)
        records.append(record)
    return pd.DataFrame.from_records(records, columns=FEATURE_COLUMNS)
