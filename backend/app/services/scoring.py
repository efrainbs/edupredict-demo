from typing import Any

import numpy as np
from sqlmodel import Session, select

from app.config import RISK_HIGH_PERCENTILE, RISK_MEDIUM_PERCENTILE
from app.models import (
    Alert,
    ModelVersion,
    RiskScore,
    Student,
    StudentFeature,
    WeeklySnapshot,
    utc_now,
)
from app.services.rules import alert_reasons
from ml.explain import main_factor_for_row, shap_matrix, top_factors_for_row
from ml.features import feature_frame


def score_students(
    session: Session,
    model: Any,
    explainer: Any,
    model_version: ModelVersion,
    thresholds: dict[str, float] | None = None,
    student_ids: set[int] | None = None,
) -> dict[str, Any]:
    students = {
        student.pseudo_id: student
        for student in session.exec(select(Student)).all()
    }
    rows = session.exec(select(StudentFeature)).all()
    if student_ids is not None:
        selected_pseudo_ids = {
            student.pseudo_id
            for student in students.values()
            if int(student.id) in student_ids
        }
        rows = [row for row in rows if row.pseudo_id in selected_pseudo_ids]

    if not rows:
        high_threshold = float(thresholds["high"]) if thresholds else 0.0
        medium_threshold = float(thresholds["medium"]) if thresholds else 0.0
        return {
            "scored": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "high_pct": 0.0,
            "medium_pct": 0.0,
            "low_pct": 0.0,
            "high_threshold": round(high_threshold, 6),
            "medium_threshold": round(medium_threshold, 6),
            "at_risk_pct": 0.0,
            "alerts_new": 0,
            "alerts_closed": 0,
        }

    frame = feature_frame(rows)
    probabilities = model.predict_proba(frame)[:, 1]

    if thresholds is None:
        high_threshold = float(np.percentile(probabilities, RISK_HIGH_PERCENTILE))
        medium_threshold = float(
            np.percentile(probabilities, RISK_MEDIUM_PERCENTILE)
        )
        model_version.threshold = {
            "high": round(high_threshold, 6),
            "medium": round(medium_threshold, 6),
        }
    else:
        high_threshold = float(thresholds["high"])
        medium_threshold = float(thresholds["medium"])

    shap_values = shap_matrix(explainer, frame)

    if student_ids is None:
        for existing in session.exec(select(RiskScore)).all():
            session.delete(existing)
    else:
        for student_id in student_ids:
            existing = session.get(RiskScore, student_id)
            if existing is not None:
                session.delete(existing)
    session.flush()

    pending_by_student: dict[int, list[Alert]] = {}
    for alert in session.exec(select(Alert)).all():
        if alert.status == "pendiente":
            pending_by_student.setdefault(alert.student_id, []).append(alert)

    now = utc_now()
    alerts_new = 0
    alerts_closed = 0

    for index, row in enumerate(rows):
        probability = float(probabilities[index])
        if probability >= high_threshold:
            level = "alto"
        elif probability >= medium_threshold:
            level = "medio"
        else:
            level = "bajo"

        shap_row = shap_values[index]
        main_factor = main_factor_for_row(shap_row, level)
        top_factors = top_factors_for_row(shap_row, row, level)
        student = students[row.pseudo_id]

        session.add(
            RiskScore(
                student_id=int(student.id),
                probability=probability,
                level=level,
                main_factor=main_factor,
                top_factors=top_factors,
                model_version_id=int(model_version.id),
                computed_at=now,
            )
        )

        pending = pending_by_student.get(int(student.id), [])
        if level in {"alto", "medio"}:
            reasons = alert_reasons(row)
            if pending:
                alert = pending[0]
                alert.level = level
                alert.main_factor = main_factor
                alert.reasons = reasons
                for extra in pending[1:]:
                    extra.status = "cerrada"
                    extra.resolved_at = now
                    alerts_closed += 1
            else:
                session.add(
                    Alert(
                        student_id=int(student.id),
                        level=level,
                        main_factor=main_factor,
                        reasons=reasons,
                        status="pendiente",
                        created_at=now,
                    )
                )
                alerts_new += 1
        else:
            for alert in pending:
                alert.status = "cerrada"
                alert.resolved_at = now
                alerts_closed += 1

    session.add(model_version)
    session.flush()

    all_scores = session.exec(select(RiskScore)).all()
    total = len(all_scores)
    counts = {"alto": 0, "medio": 0, "bajo": 0}
    for score in all_scores:
        counts[score.level] += 1

    at_risk = counts["alto"] + counts["medio"]
    at_risk_pct = round(at_risk / total * 100, 1) if total else 0.0

    snapshot = session.get(WeeklySnapshot, 8)
    if snapshot is not None:
        snapshot.projected_risk_pct = at_risk_pct
        session.add(snapshot)
        session.flush()

    return {
        "scored": len(rows),
        "high": counts["alto"],
        "medium": counts["medio"],
        "low": counts["bajo"],
        "high_pct": round(counts["alto"] / total * 100, 1) if total else 0.0,
        "medium_pct": round(counts["medio"] / total * 100, 1) if total else 0.0,
        "low_pct": round(counts["bajo"] / total * 100, 1) if total else 0.0,
        "high_threshold": round(high_threshold, 6),
        "medium_threshold": round(medium_threshold, 6),
        "at_risk_pct": at_risk_pct,
        "alerts_new": alerts_new,
        "alerts_closed": alerts_closed,
    }
