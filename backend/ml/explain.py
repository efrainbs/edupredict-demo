from typing import Any

import numpy as np
import pandas as pd
import shap
from xgboost import XGBClassifier

from ml.features import (
    FEATURE_COLUMNS,
    FEATURE_GROUPS,
    FEATURE_LABELS,
    GROUP_LABELS,
)


def build_explainer(model: XGBClassifier) -> shap.TreeExplainer:
    return shap.TreeExplainer(model)


def shap_matrix(explainer: shap.TreeExplainer, frame: pd.DataFrame) -> np.ndarray:
    values = explainer.shap_values(frame)
    if isinstance(values, list):
        values = values[1]
    matrix = np.asarray(values)
    if matrix.ndim == 3:
        matrix = matrix[:, :, -1]
    return matrix


def _percent(value: float) -> int:
    return int(round(float(value) * 100))


def factor_text(feature: str, row: Any) -> str:
    value = getattr(row, feature)

    if feature == "tuition_debt_months":
        months = int(value)
        if months == 0:
            return "Sin deuda de pensión"
        unit = "mes" if months == 1 else "meses"
        return f"Deuda de pensión de {months} {unit}"
    if feature == "weekly_work_hours":
        hours = int(value)
        if hours == 0:
            return "Sin horas de trabajo semanales"
        unit = "hora semanal" if hours == 1 else "horas semanales"
        return f"Trabaja {hours} {unit}"
    if feature == "commute_minutes":
        return f"Traslado de {int(value)} minutos"
    if feature == "gpa_avg":
        return f"Promedio de {float(value):.1f}/20"
    if feature == "grade_trend":
        if value < 0:
            return "Notas en descenso respecto al ciclo anterior"
        return "Mejora de notas respecto al ciclo anterior"
    if feature == "last_exam_grade":
        return f"Nota de último parcial: {float(value):.1f}/20"
    if feature == "failed_courses":
        courses = int(value)
        if courses == 0:
            return "Sin cursos desaprobados"
        unit = "curso desaprobado" if courses == 1 else "cursos desaprobados"
        return f"{courses} {unit}"
    if feature == "attendance_rate":
        return f"Asistencia de {_percent(value)}%"
    if feature == "consecutive_absences":
        absences = int(value)
        if absences == 0:
            return "Sin inasistencias consecutivas"
        unit = "inasistencia consecutiva" if absences == 1 else "inasistencias consecutivas"
        return f"{absences} {unit}"
    if feature == "lms_participation":
        if value < 0.6:
            return f"Baja participación en el LMS ({_percent(value)}%)"
        return f"Participación en el LMS ({_percent(value)}%)"
    if feature == "late_assignments_rate":
        return f"{_percent(value)}% de entregas tardías"
    if feature == "family_support":
        if value <= 2:
            return "Bajo apoyo familiar percibido"
        return "Apoyo familiar percibido"
    if feature == "socioemotional_adaptation":
        if value <= 2:
            return "Dificultades de adaptación socioemocional"
        return "Buena adaptación socioemocional"
    if feature == "scholarship":
        if value == 0:
            return "Sin beca"
        return "Cuenta con beca"
    if feature == "shift":
        if value == "nocturno":
            return "Estudia en turno nocturno"
        return "Estudia en turno diurno"
    if feature == "cycle":
        return f"Ciclo {int(value)}"
    if feature == "age":
        return f"Edad {int(value)}"
    return FEATURE_LABELS.get(feature, feature)


def _is_risk_direction(feature: str, row: Any) -> bool:
    value = getattr(row, feature)

    if feature == "shift":
        return value == "nocturno"
    if feature == "scholarship":
        return value == 0
    if feature in {"family_support", "socioemotional_adaptation"}:
        return value <= 2
    if feature == "grade_trend":
        return value < 0
    if feature == "attendance_rate":
        return value < 0.85
    if feature == "lms_participation":
        return value < 0.6
    if feature == "late_assignments_rate":
        return value > 0.3
    if feature == "tuition_debt_months":
        return value > 0
    if feature == "weekly_work_hours":
        return value > 15
    if feature == "commute_minutes":
        return value > 45
    if feature == "failed_courses":
        return value > 0
    if feature == "consecutive_absences":
        return value > 0
    if feature == "last_exam_grade":
        return value < 13
    if feature == "gpa_avg":
        return value < 13
    return True


def main_factor_for_row(shap_row: np.ndarray, level: str) -> str:
    if level == "bajo":
        return "Ninguno"

    group_scores = {group: 0.0 for group in GROUP_LABELS}
    for feature, impact in zip(FEATURE_COLUMNS, shap_row):
        if impact > 0:
            group_scores[FEATURE_GROUPS[feature]] += float(impact)

    best_group = max(group_scores, key=group_scores.get)
    if group_scores[best_group] <= 0:
        return "Ninguno"
    return GROUP_LABELS[best_group]


def top_factors_for_row(
    shap_row: np.ndarray, row: Any, level: str
) -> list[dict[str, Any]]:
    if level == "bajo":
        return []

    ranked = sorted(
        zip(FEATURE_COLUMNS, shap_row),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    chosen = [
        (feature, impact)
        for feature, impact in ranked
        if impact > 0 and _is_risk_direction(feature, row)
    ][:3]

    if len(chosen) < 3:
        chosen_features = {feature for feature, _ in chosen}
        for feature, impact in ranked:
            if feature not in chosen_features and impact > 0:
                chosen.append((feature, impact))
                chosen_features.add(feature)
            if len(chosen) == 3:
                break

    if len(chosen) < 3:
        chosen_features = {feature for feature, _ in chosen}
        for feature, impact in ranked:
            if feature not in chosen_features:
                chosen.append((feature, impact))
                chosen_features.add(feature)
            if len(chosen) == 3:
                break

    return [
        {
            "feature": feature,
            "group": FEATURE_GROUPS[feature],
            "impact": round(float(impact), 4),
            "text": factor_text(feature, row),
        }
        for feature, impact in chosen
    ]
