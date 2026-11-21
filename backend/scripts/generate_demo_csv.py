from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR  # noqa: E402
from app.db import engine  # noqa: E402
from app.models import Career, Student, StudentFeature, Tutor  # noqa: E402
from ml.features import FEATURE_COLUMNS  # noqa: E402
from ml.generate_data import (  # noqa: E402
    FEMALE_NAMES,
    MALE_NAMES,
    SURNAMES,
    generate_features,
)

SEED = 2026
N_WORSENED = 120
N_UNCHANGED = 60
N_NEW = 15
DIEGO_NAME = "Diego Torres Ruiz"
OUTPUT_PATH = DATA_DIR / "demo_upload.csv"

COLUMNS = [
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

DIEGO_FEATURES = {
    "gpa_avg": 7.0,
    "grade_trend": -4.5,
    "last_exam_grade": 5.0,
    "failed_courses": 6,
    "attendance_rate": 0.45,
    "consecutive_absences": 8,
    "lms_participation": 0.10,
    "late_assignments_rate": 0.80,
    "tuition_debt_months": 4,
    "scholarship": 0,
    "weekly_work_hours": 30,
    "commute_minutes": 120,
    "family_support": 1,
    "socioemotional_adaptation": 1,
    "shift": "nocturno",
    "cycle": 2,
    "age": 21,
}


def _feature_dict(feature: StudentFeature) -> dict:
    return {name: getattr(feature, name) for name in FEATURE_COLUMNS}


def _worsen(features: dict, rng: np.random.Generator) -> dict:
    worsened = dict(features)
    worsened["gpa_avg"] = round(
        max(0.0, features["gpa_avg"] - rng.uniform(2.0, 4.0)), 2
    )
    worsened["grade_trend"] = round(
        max(-5.0, features["grade_trend"] - rng.uniform(1.0, 2.5)), 2
    )
    worsened["last_exam_grade"] = round(
        max(0.0, features["last_exam_grade"] - rng.uniform(2.0, 4.0)), 2
    )
    worsened["failed_courses"] = min(
        6, int(features["failed_courses"]) + int(rng.choice([1, 2]))
    )
    worsened["attendance_rate"] = round(
        min(1.0, max(0.0, features["attendance_rate"] * rng.uniform(0.65, 0.85))),
        3,
    )
    worsened["consecutive_absences"] = min(
        10, int(features["consecutive_absences"]) + int(rng.choice([1, 2, 3]))
    )
    worsened["lms_participation"] = round(
        min(1.0, max(0.0, features["lms_participation"] * rng.uniform(0.4, 0.7))),
        3,
    )
    worsened["late_assignments_rate"] = round(
        min(1.0, features["late_assignments_rate"] + rng.uniform(0.1, 0.25)),
        3,
    )
    worsened["tuition_debt_months"] = min(
        4, int(features["tuition_debt_months"]) + int(rng.choice([1, 2]))
    )
    worsened["weekly_work_hours"] = min(
        48, int(features["weekly_work_hours"]) + int(rng.choice([0, 5, 10]))
    )
    worsened["commute_minutes"] = min(
        150, int(features["commute_minutes"]) + int(rng.choice([0, 10, 20]))
    )
    worsened["family_support"] = max(1, int(features["family_support"]) - 1)
    worsened["socioemotional_adaptation"] = max(
        1, int(features["socioemotional_adaptation"]) - 1
    )
    return worsened


def _row(
    student: Student,
    features: dict,
    career_name: str,
    tutor_name: str,
) -> dict:
    row = {
        "student_code": student.code,
        "full_name": student.full_name,
        "gender": student.gender,
        "career": career_name,
        "tutor_name": tutor_name,
    }
    row.update({name: features[name] for name in FEATURE_COLUMNS})
    return row


def _new_row(
    code: str,
    name: str,
    gender: str,
    career_name: str,
    tutor_name: str,
    features: dict,
) -> dict:
    row = {
        "student_code": code,
        "full_name": name,
        "gender": gender,
        "career": career_name,
        "tutor_name": tutor_name,
    }
    row.update({name: features[name] for name in FEATURE_COLUMNS})
    return row


def _unique_name(rng: np.random.Generator, used: set[str], gender: str) -> str:
    pool = FEMALE_NAMES if gender == "F" else MALE_NAMES
    while True:
        name = f"{rng.choice(pool)} {rng.choice(SURNAMES)} {rng.choice(SURNAMES)}"
        if name not in used:
            used.add(name)
            return name


def build_rows() -> list[dict]:
    rng = np.random.default_rng(SEED)

    with Session(engine) as session:
        students = session.exec(select(Student).order_by(Student.id)).all()
        features = {
            feature.pseudo_id: feature
            for feature in session.exec(select(StudentFeature)).all()
        }
        careers = {career.id: career.name for career in session.exec(select(Career)).all()}
        tutors = {tutor.id: tutor.name for tutor in session.exec(select(Tutor)).all()}

    if not students:
        raise SystemExit("No hay estudiantes. Ejecuta `make seed` primero.")

    by_name = {student.full_name: student for student in students}
    diego = by_name.get(DIEGO_NAME)
    if diego is None:
        raise SystemExit("No se encontró a Diego Torres Ruiz en la base de datos.")

    others = [student for student in students if student.id != diego.id]
    indices = rng.permutation(len(others))
    worsened_others = [others[index] for index in indices[: N_WORSENED - 1]]
    unchanged = [
        others[index] for index in indices[N_WORSENED - 1 : N_WORSENED - 1 + N_UNCHANGED]
    ]

    rows: list[dict] = []

    diego_row = _row(
        diego,
        DIEGO_FEATURES,
        careers[diego.career_id],
        tutors[diego.tutor_id],
    )
    rows.append(diego_row)

    for student in worsened_others:
        original = _feature_dict(features[student.pseudo_id])
        rows.append(
            _row(
                student,
                _worsen(original, rng),
                careers[student.career_id],
                tutors[student.tutor_id],
            )
        )

    for student in unchanged:
        original = _feature_dict(features[student.pseudo_id])
        rows.append(
            _row(
                student,
                original,
                careers[student.career_id],
                tutors[student.tutor_id],
            )
        )

    used_names = {student.full_name for student in students}
    career_names = list(careers.values())
    tutor_names = list(tutors.values())
    new_features = generate_features(rng, N_NEW)
    for index in range(N_NEW):
        gender = "F" if rng.random() < 0.5 else "M"
        code = f"U0090{index + 1:04d}"
        name = _unique_name(rng, used_names, gender)
        new_row_features = {
            field: new_features[field][index] for field in FEATURE_COLUMNS
        }
        new_row_features["shift"] = str(new_row_features["shift"])
        for field in FEATURE_COLUMNS:
            value = new_row_features[field]
            if field == "shift":
                continue
            if isinstance(value, (np.integer,)):
                new_row_features[field] = int(value)
            elif isinstance(value, (np.floating,)):
                new_row_features[field] = float(value)
        rows.append(
            _new_row(
                code,
                name,
                gender,
                str(rng.choice(career_names)),
                str(rng.choice(tutor_names)),
                new_row_features,
            )
        )

    invalid_sources = [
        others[index] for index in indices[N_WORSENED + N_UNCHANGED :][:3]
    ]
    corruptions = [
        ("attendance_rate", 1.4),
        ("shift", "matutino"),
        ("career", "Ingeniería Aeroespacial"),
    ]
    for student, (column, value) in zip(invalid_sources, corruptions):
        row = _row(
            student,
            _feature_dict(features[student.pseudo_id]),
            careers[student.career_id],
            tutors[student.tutor_id],
        )
        row[column] = value
        rows.append(row)

    return rows


def main() -> None:
    rows = build_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"demo_upload.csv generado: {OUTPUT_PATH}")
    print(f"  filas: {len(rows)} (3 inválidas incluidas)")


if __name__ == "__main__":
    main()
