from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from sqlmodel import Session, select
from xgboost import XGBClassifier

from app.models import (
    Career,
    ModelVersion,
    PipelineRun,
    RiskScore,
    Student,
    StudentFeature,
    Tutor,
    utc_now,
)
from app.services.pseudonymize import pseudo_id_for
from app.services.scoring import score_students
from ml.explain import build_explainer
from ml.features import FEATURE_COLUMNS
from ml.train import ARTIFACTS_DIR

MAX_UPLOAD_BYTES = 5 * 1024 * 1024

CSV_COLUMNS = [
    "student_code",
    "full_name",
    "gender",
    "career",
    "cycle",
    "tutor_name",
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
    "age",
]

FLOAT_RANGES = {
    "gpa_avg": (0.0, 20.0),
    "grade_trend": (-5.0, 5.0),
    "last_exam_grade": (0.0, 20.0),
    "attendance_rate": (0.0, 1.0),
    "lms_participation": (0.0, 1.0),
    "late_assignments_rate": (0.0, 1.0),
}

INT_RANGES = {
    "failed_courses": (0, 6),
    "consecutive_absences": (0, 10),
    "tuition_debt_months": (0, 4),
    "scholarship": (0, 1),
    "weekly_work_hours": (0, 48),
    "commute_minutes": (5, 150),
    "family_support": (1, 5),
    "socioemotional_adaptation": (1, 5),
    "cycle": (1, 6),
    "age": (17, 40),
}

SHIFT_VALUES = {"diurno", "nocturno"}
GENDER_VALUES = {"F", "M"}

DISTRIBUTION_KEYS = {"alto": "high", "medio": "medium", "bajo": "low"}


class CsvValidationError(ValueError):
    """Raised when the uploaded file cannot be processed as a CSV."""


class ModelUnavailableError(RuntimeError):
    """Raised when there is no trained model to score the upload."""


class _RowError(Exception):
    def __init__(self, column: str, reason: str) -> None:
        super().__init__(reason)
        self.column = column
        self.reason = reason


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _required(raw: dict[str, Any], column: str) -> str:
    value = _clean(raw.get(column))
    if not value:
        raise _RowError(column, "Campo obligatorio")
    return value


def _parse_float(raw: dict[str, Any], column: str) -> float:
    value = _required(raw, column)
    try:
        number = float(value)
    except ValueError:
        raise _RowError(column, f"Valor no numérico ({value})") from None
    low, high = FLOAT_RANGES[column]
    if not low <= number <= high:
        raise _RowError(column, f"Valor fuera de rango ({value})")
    return number


def _parse_int(raw: dict[str, Any], column: str) -> int:
    value = _required(raw, column)
    try:
        number = float(value)
    except ValueError:
        raise _RowError(column, f"Valor no numérico ({value})") from None
    if not number.is_integer():
        raise _RowError(column, f"Debe ser un entero ({value})")
    integer = int(number)
    low, high = INT_RANGES[column]
    if not low <= integer <= high:
        raise _RowError(column, f"Valor fuera de rango ({value})")
    return integer


def _validate_row(
    raw: dict[str, Any],
    line_number: int,
    careers: dict[str, Career],
    tutors: dict[str, Tutor],
    existing_codes: set[str],
    seen_codes: set[str],
) -> dict[str, Any]:
    code = _required(raw, "student_code")
    if code in seen_codes:
        raise _RowError("student_code", "Código duplicado en el archivo")
    seen_codes.add(code)

    full_name = _required(raw, "full_name")
    gender = _required(raw, "gender").upper()
    if gender not in GENDER_VALUES:
        raise _RowError("gender", f"Valor no permitido ({gender})")

    career_name = _required(raw, "career")
    career = careers.get(career_name)
    if career is None:
        raise _RowError("career", f"Carrera no encontrada ({career_name})")

    cycle = _parse_int(raw, "cycle")

    tutor_id: int | None = None
    if code not in existing_codes:
        tutor_name = _required(raw, "tutor_name")
        tutor = tutors.get(tutor_name)
        if tutor is None:
            raise _RowError("tutor_name", f"Tutor no encontrado ({tutor_name})")
        tutor_id = int(tutor.id)

    features: dict[str, Any] = {}
    for field in FEATURE_COLUMNS:
        if field == "shift":
            shift = _required(raw, "shift").lower()
            if shift not in SHIFT_VALUES:
                raise _RowError("shift", f"Valor no permitido ({shift})")
            features[field] = shift
        elif field == "cycle":
            features[field] = cycle
        elif field in INT_RANGES:
            features[field] = _parse_int(raw, field)
        else:
            features[field] = _parse_float(raw, field)

    return {
        "row": line_number,
        "code": code,
        "full_name": full_name,
        "gender": gender,
        "career_id": int(career.id),
        "tutor_id": tutor_id,
        "features": features,
    }


def _apply_rows(
    session: Session,
    rows: list[dict[str, Any]],
    existing: dict[str, Student],
) -> None:
    now = utc_now()
    for row in rows:
        student = existing.get(row["code"])
        if student is None:
            student = Student(
                code=row["code"],
                full_name=row["full_name"],
                gender=row["gender"],
                career_id=row["career_id"],
                cycle=int(row["features"]["cycle"]),
                tutor_id=int(row["tutor_id"]),
                pseudo_id=pseudo_id_for(row["code"]),
            )
            session.add(student)
            existing[row["code"]] = student
        else:
            student.full_name = row["full_name"]
            student.gender = row["gender"]
            student.career_id = row["career_id"]
            student.cycle = int(row["features"]["cycle"])

        feature = session.get(StudentFeature, student.pseudo_id)
        if feature is None:
            feature = StudentFeature(pseudo_id=student.pseudo_id)
        for field, value in row["features"].items():
            setattr(feature, field, value)
        feature.updated_at = now
        session.add(feature)

    session.flush()


def _distribution(session: Session) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for score in session.exec(select(RiskScore)).all():
        key = DISTRIBUTION_KEYS.get(score.level)
        if key is not None:
            counts[key] += 1
    return counts


def _model_view_row(feature: StudentFeature) -> dict[str, Any]:
    row: dict[str, Any] = {"pseudo_id": feature.pseudo_id}
    for field in FEATURE_COLUMNS:
        row[field] = getattr(feature, field)
    return row


def _model_view_sample(
    session: Session, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    sample: list[dict[str, Any]] = []
    for row in rows[:3]:
        feature = session.get(
            StudentFeature, pseudo_id_for(row["code"])
        )
        if feature is not None:
            sample.append(_model_view_row(feature))

    if len(sample) < 3:
        for feature in session.exec(
            select(StudentFeature).order_by(StudentFeature.pseudo_id)
        ).all():
            if len(sample) == 3:
                break
            if any(item["pseudo_id"] == feature.pseudo_id for item in sample):
                continue
            sample.append(_model_view_row(feature))
    return sample[:3]


def _load_model() -> tuple[XGBClassifier, Any]:
    path = Path(ARTIFACTS_DIR) / "xgb_model.json"
    if not path.exists():
        raise ModelUnavailableError(
            "No hay un modelo entrenado. Ejecuta `make train` primero."
        )
    model = XGBClassifier()
    model.load_model(path)
    return model, build_explainer(model)


def process_upload(
    session: Session,
    content: str,
    source: str = "upload",
) -> dict[str, Any]:
    active = session.exec(
        select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
    ).first()
    if active is None:
        raise ModelUnavailableError(
            "No hay un modelo entrenado. Ejecuta `make train` primero."
        )

    thresholds = active.threshold or {}
    if "high" not in thresholds or "medium" not in thresholds:
        raise ModelUnavailableError(
            "El modelo activo no tiene umbrales calibrados."
        )

    model, explainer = _load_model()

    careers = {career.name: career for career in session.exec(select(Career)).all()}
    tutors = {tutor.name: tutor for tutor in session.exec(select(Tutor)).all()}
    existing = {
        student.code: student for student in session.exec(select(Student)).all()
    }

    distribution_before = _distribution(session)

    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []
    missing = [column for column in CSV_COLUMNS if column not in fieldnames]
    if missing:
        raise CsvValidationError(
            "Faltan columnas obligatorias: " + ", ".join(missing)
        )

    raw_rows = [
        row
        for row in reader
        if any(_clean(value) for value in row.values())
    ]

    steps: list[dict[str, str]] = [
        {
            "key": "ingest",
            "label": "Ingesta",
            "detail": f"{len(raw_rows)} filas recibidas",
        }
    ]

    valid_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_codes: set[str] = set()

    for index, raw in enumerate(raw_rows):
        line_number = index + 2
        try:
            valid_rows.append(
                _validate_row(
                    raw,
                    line_number,
                    careers,
                    tutors,
                    set(existing),
                    seen_codes,
                )
            )
        except _RowError as error:
            errors.append(
                {
                    "row": line_number,
                    "column": error.column,
                    "reason": error.reason,
                }
            )

    steps.append(
        {
            "key": "clean",
            "label": "Limpieza y validación",
            "detail": (
                f"{len(valid_rows)} válidas, {len(errors)} rechazadas"
            ),
        }
    )

    _apply_rows(session, valid_rows, existing)
    affected_ids = {
        int(existing[row["code"]].id)
        for row in valid_rows
        if existing[row["code"]].id is not None
    }

    steps.append(
        {
            "key": "pseudonymize",
            "label": "Seudonimización",
            "detail": (
                f"{len(valid_rows)} identificadores reemplazados por seudónimos"
            ),
        }
    )

    summary = score_students(
        session,
        model,
        explainer,
        active,
        thresholds={
            "high": float(thresholds["high"]),
            "medium": float(thresholds["medium"]),
        },
        student_ids=affected_ids,
    )

    steps.append(
        {
            "key": "score",
            "label": "Puntuación",
            "detail": (
                f"{summary['scored']} estudiantes puntuados con "
                f"modelo v{active.id}"
            ),
        }
    )
    steps.append(
        {
            "key": "alerts",
            "label": "Alertas",
            "detail": (
                f"{summary['alerts_new']} nuevas, "
                f"{summary['alerts_closed']} cerradas"
            ),
        }
    )

    distribution_after = _distribution(session)
    model_view_sample = _model_view_sample(session, valid_rows)

    run = PipelineRun(
        source=source,
        steps=steps,
        distribution_before=distribution_before,
        distribution_after=distribution_after,
    )
    session.add(run)
    session.flush()
    session.commit()

    return {
        "run_id": int(run.id),
        "steps": steps,
        "errors": errors,
        "distribution_before": distribution_before,
        "distribution_after": distribution_after,
        "model_view_sample": model_view_sample,
    }
