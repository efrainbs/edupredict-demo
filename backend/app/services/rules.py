from typing import Any


def alert_reasons(features: Any) -> list[str]:
    reasons: list[str] = []

    if features.consecutive_absences >= 3:
        reasons.append(f"{features.consecutive_absences} inasistencias consecutivas")
    if features.last_exam_grade <= 10:
        reasons.append(f"Nota de parcial: {features.last_exam_grade:.1f}/20")
    if features.tuition_debt_months >= 2:
        months = features.tuition_debt_months
        unit = "mes" if months == 1 else "meses"
        reasons.append(f"Deuda pendiente ({months} {unit})")
    if features.lms_participation < 0.30:
        reasons.append("Baja participación en LMS")
    if features.grade_trend <= -2:
        reasons.append("Pérdida de promedio")

    return reasons[:2]
