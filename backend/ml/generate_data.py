from __future__ import annotations

from typing import Any

import bcrypt
import numpy as np
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, select

from app.db import engine
from app.models import (
    Career,
    Faculty,
    HistoricalCohort,
    Student,
    StudentFeature,
    Tutor,
    User,
    WeeklySnapshot,
)
from app.services.pseudonymize import pseudo_id_for

SEED = 42
N_HISTORICAL = 4000
N_STUDENTS = 1500
N_TUTORS = 20
STUDENTS_PER_TUTOR = 75
NOISE_SD = 0.7
TARGET_DROPOUT_RATE = 0.175
DEMO_PASSWORD = "demo1234"

FEATURE_NAMES = (
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
)

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

FACULTY_CAREERS = {
    "Ingeniería": ["Ing. de Software", "Ing. Industrial"],
    "Negocios": ["Administración", "Contabilidad"],
    "Salud": ["Enfermería", "Farmacia"],
    "Artes y Diseño": ["Diseño Gráfico", "Diseño de Interiores"],
}

CAREER_COUNTS = {
    "Ing. de Software": 263,
    "Ing. Industrial": 262,
    "Administración": 263,
    "Contabilidad": 262,
    "Enfermería": 135,
    "Farmacia": 135,
    "Diseño Gráfico": 90,
    "Diseño de Interiores": 90,
}

TUTOR_NAMES = [
    "Roberto Díaz",
    "Mariela Salazar",
    "Patricia Núñez",
    "Jorge Salinas",
    "Lucía Herrera",
    "Miguel Paredes",
    "Rosa Chávez",
    "Fernando Rojas",
    "Elena Vargas",
    "Raúl Medina",
    "Camila Ortiz",
    "Sergio Palacios",
    "Daniela Cruz",
    "Andrés Castillo",
    "Paola Rivera",
    "Hugo Guzmán",
    "Natalia Cáceres",
    "Marco Espinoza",
    "Verónica Ramos",
    "Esteban Aguilar",
]

FEMALE_NAMES = [
    "Ana",
    "Sofía",
    "Valeria",
    "Camila",
    "María",
    "Lucía",
    "Daniela",
    "Fernanda",
    "Claudia",
    "Rosa",
    "Elena",
    "Paola",
    "Gabriela",
    "Andrea",
    "Carolina",
    "Natalia",
    "Isabel",
    "Verónica",
    "Milagros",
    "Patricia",
]

MALE_NAMES = [
    "Carlos",
    "Luis",
    "Diego",
    "Jorge",
    "José",
    "Miguel",
    "Juan",
    "Pedro",
    "Andrés",
    "Ricardo",
    "Fernando",
    "Sergio",
    "Óscar",
    "Raúl",
    "Hugo",
    "Marco",
    "Alonso",
    "Bruno",
    "Esteban",
    "Renzo",
]

SURNAMES = [
    "Mendoza",
    "Quispe",
    "Flores",
    "Rojas",
    "Huamán",
    "Castro",
    "Torres",
    "Vega",
    "Mamani",
    "Ríos",
    "Salazar",
    "Vargas",
    "Chávez",
    "García",
    "Paredes",
    "Sánchez",
    "Ramírez",
    "Cruz",
    "Ortiz",
    "Medina",
    "Palacios",
    "Castillo",
    "Rivera",
    "Guzmán",
    "Cáceres",
    "Espinoza",
    "Ramos",
    "Herrera",
    "Aguilar",
    "Soto",
]

CURATED_STUDENTS = [
    {
        "full_name": "Carlos Mendoza Ríos",
        "gender": "M",
        "career": "Ing. de Software",
        "features": {
            "gpa_avg": 8.2,
            "grade_trend": -3.6,
            "last_exam_grade": 7.0,
            "failed_courses": 4,
            "attendance_rate": 0.70,
            "consecutive_absences": 3,
            "lms_participation": 0.28,
            "late_assignments_rate": 0.62,
            "tuition_debt_months": 2,
            "scholarship": 0,
            "weekly_work_hours": 18,
            "commute_minutes": 75,
            "family_support": 2,
            "socioemotional_adaptation": 2,
            "shift": "diurno",
            "cycle": 3,
            "age": 20,
        },
    },
    {
        "full_name": "Ana López Silva",
        "gender": "F",
        "career": "Administración",
        "features": {
            "gpa_avg": 12.0,
            "grade_trend": -1.2,
            "last_exam_grade": 11.0,
            "failed_courses": 2,
            "attendance_rate": 0.76,
            "consecutive_absences": 2,
            "lms_participation": 0.36,
            "late_assignments_rate": 0.45,
            "tuition_debt_months": 4,
            "scholarship": 0,
            "weekly_work_hours": 42,
            "commute_minutes": 130,
            "family_support": 2,
            "socioemotional_adaptation": 3,
            "shift": "nocturno",
            "cycle": 4,
            "age": 27,
        },
    },
    {
        "full_name": "Luis Quispe Mamani",
        "gender": "M",
        "career": "Ing. Industrial",
        "features": {
            "gpa_avg": 12.8,
            "grade_trend": -1.4,
            "last_exam_grade": 10.5,
            "failed_courses": 2,
            "attendance_rate": 0.73,
            "consecutive_absences": 4,
            "lms_participation": 0.42,
            "late_assignments_rate": 0.40,
            "tuition_debt_months": 1,
            "scholarship": 0,
            "weekly_work_hours": 18,
            "commute_minutes": 70,
            "family_support": 3,
            "socioemotional_adaptation": 3,
            "shift": "diurno",
            "cycle": 2,
            "age": 21,
        },
    },
    {
        "full_name": "Sofía Castro Vega",
        "gender": "F",
        "career": "Enfermería",
        "features": {
            "gpa_avg": 12.0,
            "grade_trend": -1.0,
            "last_exam_grade": 12.0,
            "failed_courses": 1,
            "attendance_rate": 0.78,
            "consecutive_absences": 2,
            "lms_participation": 0.35,
            "late_assignments_rate": 0.30,
            "tuition_debt_months": 3,
            "scholarship": 1,
            "weekly_work_hours": 12,
            "commute_minutes": 45,
            "family_support": 1,
            "socioemotional_adaptation": 1,
            "shift": "diurno",
            "cycle": 3,
            "age": 20,
        },
    },
    {
        "full_name": "Diego Torres Ruiz",
        "gender": "M",
        "career": "Diseño Gráfico",
        "features": {
            "gpa_avg": 15.8,
            "grade_trend": 0.6,
            "last_exam_grade": 16.0,
            "failed_courses": 0,
            "attendance_rate": 0.93,
            "consecutive_absences": 0,
            "lms_participation": 0.72,
            "late_assignments_rate": 0.12,
            "tuition_debt_months": 0,
            "scholarship": 1,
            "weekly_work_hours": 0,
            "commute_minutes": 30,
            "family_support": 4,
            "socioemotional_adaptation": 4,
            "shift": "diurno",
            "cycle": 2,
            "age": 19,
        },
    },
]

REAL_DROPOUT_PCT = [2.1, 2.8, 3.4, 4.2, 5.0, 5.9, 6.8, 7.7]
PROJECTED_RISK_PCT = [18.0, 18.8, 19.7, 20.6, 21.6, 22.7, 23.8, 25.0]


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-values))


def _calibrate_intercept(base: np.ndarray, target: float) -> float:
    low, high = -10.0, 10.0
    for _ in range(80):
        mid = (low + high) / 2.0
        if _sigmoid(base + mid).mean() < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def generate_features(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    ability = rng.normal(0, 1, n)
    engagement = rng.normal(0, 1, n)
    stress = rng.normal(0, 1, n)

    gpa_avg = np.clip(
        13 + 2.2 * ability + 0.8 * engagement + rng.normal(0, 0.8, n), 0, 20
    )
    last_exam_grade = np.clip(gpa_avg + rng.normal(0, 2, n), 0, 20)
    grade_trend = np.clip(
        0.8 * (engagement + ability) / 2 + rng.normal(0, 1, n), -5, 5
    )

    failed_lambda = np.maximum(0.3, 1.2 - 0.5 * ability - 0.3 * engagement)
    failed_courses = np.clip(rng.poisson(failed_lambda), 0, 6)

    attendance_rate = np.clip(
        0.85 + 0.07 * engagement - 0.03 * stress + rng.normal(0, 0.05, n), 0, 1
    )
    absence_lambda = np.maximum(0, 1 - 0.8 * engagement + 0.3 * stress)
    consecutive_absences = np.clip(rng.poisson(absence_lambda), 0, 10)

    lms_participation = np.clip(
        0.6 + 0.15 * engagement + rng.normal(0, 0.1, n), 0, 1
    )
    late_assignments_rate = np.clip(
        0.2 - 0.08 * engagement + rng.normal(0, 0.07, n), 0, 1
    )

    debt_signal = stress + rng.normal(0, 0.5, n)
    tuition_debt_months = np.select(
        [debt_signal < 0.2, debt_signal < 0.8, debt_signal < 1.4, debt_signal < 2.0],
        [0, 1, 2, 3],
        default=4,
    ).astype(int)

    weekly_work_hours = np.clip(
        np.round(np.maximum(0, 12 + 9 * stress + rng.normal(0, 6, n))), 0, 48
    ).astype(int)
    weekly_work_hours[rng.random(n) < 0.25] = 0

    night_probability = np.clip(0.05 + weekly_work_hours / 100, 0.03, 0.60)
    is_night = rng.random(n) < night_probability
    shift = np.where(is_night, "nocturno", "diurno")

    age = np.where(
        is_night,
        rng.integers(20, 35, n),
        rng.integers(18, 23, n),
    )
    age = np.clip(age, 17, 40).astype(int)

    scholarship_probability = np.clip(
        0.25 + 0.10 * ability + 0.08 * stress, 0.05, 0.65
    )
    scholarship = (rng.random(n) < scholarship_probability).astype(int)

    commute_minutes = np.clip(
        np.round(50 + 15 * stress + rng.normal(0, 20, n)), 5, 150
    ).astype(int)

    support_base = 3 - 0.6 * stress + 0.5 * engagement + rng.normal(0, 0.8, n)
    family_support = np.clip(np.round(support_base), 1, 5).astype(int)
    socioemotional_adaptation = np.clip(
        np.round(3 - 0.6 * stress + 0.5 * engagement + rng.normal(0, 0.8, n)), 1, 5
    ).astype(int)

    cycle = rng.integers(1, 7, n)

    return {
        "gpa_avg": np.round(gpa_avg, 2),
        "grade_trend": np.round(grade_trend, 2),
        "last_exam_grade": np.round(last_exam_grade, 2),
        "failed_courses": failed_courses.astype(int),
        "attendance_rate": np.round(attendance_rate, 3),
        "consecutive_absences": consecutive_absences.astype(int),
        "lms_participation": np.round(lms_participation, 3),
        "late_assignments_rate": np.round(late_assignments_rate, 3),
        "tuition_debt_months": tuition_debt_months,
        "scholarship": scholarship,
        "weekly_work_hours": weekly_work_hours,
        "commute_minutes": commute_minutes,
        "family_support": family_support,
        "socioemotional_adaptation": socioemotional_adaptation,
        "shift": shift,
        "cycle": cycle,
        "age": age,
    }


def build_historical_cohort(
    rng: np.random.Generator,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    features = generate_features(rng, N_HISTORICAL)

    z_base = (
        -0.25 * (features["gpa_avg"] - 13)
        - 0.30 * features["grade_trend"]
        + 0.35 * features["failed_courses"]
        - 3.0 * (features["attendance_rate"] - 0.85)
        + 0.25 * np.maximum(features["consecutive_absences"] - 1, 0)
        - 1.5 * (features["lms_participation"] - 0.6)
        + 0.8 * (features["late_assignments_rate"] - 0.2)
        + 0.55 * features["tuition_debt_months"]
        + 0.04 * np.maximum(features["weekly_work_hours"] - 15, 0)
        + 0.008 * np.maximum(features["commute_minutes"] - 45, 0)
        - 0.35 * (features["family_support"] - 3)
        - 0.40 * (features["socioemotional_adaptation"] - 3)
        - 0.5 * features["scholarship"]
        + 0.30 * (features["shift"] == "nocturno")
    )
    intercept = _calibrate_intercept(z_base, TARGET_DROPOUT_RATE)
    probability = _sigmoid(z_base + intercept + rng.normal(0, NOISE_SD, N_HISTORICAL))
    dropped_out = (rng.random(N_HISTORICAL) < probability).astype(int)

    return features, dropped_out


def _unique_name(
    rng: np.random.Generator, gender: str, used_names: set[str]
) -> str:
    first_names = FEMALE_NAMES if gender == "F" else MALE_NAMES
    while True:
        name = (
            f"{rng.choice(first_names)} "
            f"{rng.choice(SURNAMES)} "
            f"{rng.choice(SURNAMES)}"
        )
        if name not in used_names:
            used_names.add(name)
            return name


def build_current_students(
    rng: np.random.Generator,
    career_ids: dict[str, int],
    tutor_ids: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    features = generate_features(rng, N_STUDENTS)

    career_pool: list[int] = []
    for career_name, count in CAREER_COUNTS.items():
        career_pool.extend([career_ids[career_name]] * count)
    rng.shuffle(career_pool)

    tutor_pool = np.repeat(
        np.array([tutor_ids[name] for name in TUTOR_NAMES]), STUDENTS_PER_TUTOR
    )
    rng.shuffle(tutor_pool)

    used_names = {student["full_name"] for student in CURATED_STUDENTS}
    full_names: list[str] = []
    genders: list[str] = []

    for index in range(N_STUDENTS):
        if index < len(CURATED_STUDENTS):
            curated = CURATED_STUDENTS[index]
            gender = curated["gender"]
            full_name = curated["full_name"]
            career_id = career_ids[curated["career"]]
            tutor_id = tutor_ids["Roberto Díaz"]
            for feature_name, value in curated["features"].items():
                features[feature_name][index] = value
        else:
            gender = "F" if rng.random() < 0.5 else "M"
            full_name = _unique_name(rng, gender, used_names)
            career_id = int(career_pool[index])
            tutor_id = int(tutor_pool[index])

        full_names.append(full_name)
        genders.append(gender)
        career_pool[index] = career_id
        tutor_pool[index] = tutor_id

    records = []
    for index in range(N_STUDENTS):
        code = f"U{index + 1:08d}"
        records.append(
            {
                "code": code,
                "full_name": full_names[index],
                "gender": genders[index],
                "career_id": int(career_pool[index]),
                "cycle": int(features["cycle"][index]),
                "tutor_id": int(tutor_pool[index]),
                "pseudo_id": pseudo_id_for(code),
            }
        )

    return records, features


def _feature_values(features: dict[str, np.ndarray], index: int) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in FEATURE_NAMES:
        value = features[name][index]
        if name == "shift":
            values[name] = str(value)
        elif name in INTEGER_FEATURES:
            values[name] = int(value)
        else:
            values[name] = float(value)
    return values


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_database(engine: Engine) -> dict[str, Any]:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    rng = np.random.default_rng(SEED)

    with Session(engine) as session:
        faculties = [Faculty(name=name) for name in FACULTY_CAREERS]
        tutors = [Tutor(name=name) for name in TUTOR_NAMES]
        session.add_all(faculties)
        session.add_all(tutors)
        session.flush()

        faculty_ids = {faculty.name: faculty.id for faculty in faculties}
        career_rows = []
        for faculty_name, career_names in FACULTY_CAREERS.items():
            for career_name in career_names:
                career_rows.append(
                    Career(
                        name=career_name,
                        faculty_id=int(faculty_ids[faculty_name]),
                    )
                )
        session.add_all(career_rows)
        session.flush()

        career_ids = {career.name: career.id for career in career_rows}
        tutor_ids = {tutor.name: tutor.id for tutor in tutors}

        historical_features, dropped_out = build_historical_cohort(rng)
        historical_rows = [
            HistoricalCohort(
                **_feature_values(historical_features, index),
                dropped_out=int(dropped_out[index]),
            )
            for index in range(N_HISTORICAL)
        ]

        student_records, student_feature_values = build_current_students(
            rng, career_ids, tutor_ids
        )
        student_rows = [Student(**record) for record in student_records]
        student_feature_rows = [
            StudentFeature(
                pseudo_id=record["pseudo_id"],
                **_feature_values(student_feature_values, index),
            )
            for index, record in enumerate(student_records)
        ]

        users = [
            User(
                email="director@edupredict.demo",
                name="Dirección Académica",
                role="director",
                password_hash=_hash_password(DEMO_PASSWORD),
                tutor_id=None,
            ),
            User(
                email="tutor1@edupredict.demo",
                name="Prof. Roberto Díaz",
                role="tutor",
                password_hash=_hash_password(DEMO_PASSWORD),
                tutor_id=int(tutor_ids["Roberto Díaz"]),
            ),
            User(
                email="tutor2@edupredict.demo",
                name="Prof. Mariela Salazar",
                role="tutor",
                password_hash=_hash_password(DEMO_PASSWORD),
                tutor_id=int(tutor_ids["Mariela Salazar"]),
            ),
        ]

        snapshots = [
            WeeklySnapshot(
                week_index=index + 1,
                real_dropout_pct=REAL_DROPOUT_PCT[index],
                projected_risk_pct=PROJECTED_RISK_PCT[index],
            )
            for index in range(8)
        ]

        session.add_all(historical_rows)
        session.add_all(student_rows)
        session.flush()
        session.add_all(student_feature_rows)
        session.add_all(users)
        session.add_all(snapshots)
        session.commit()

        prevalence = float(dropped_out.mean())
        return {
            "faculties": len(faculties),
            "careers": len(career_rows),
            "tutors": len(tutors),
            "students": len(student_rows),
            "student_features": len(student_feature_rows),
            "historical_cohort": len(historical_rows),
            "dropout_prevalence": round(prevalence, 4),
            "users": len(users),
            "weekly_snapshots": len(snapshots),
        }


def print_sample(engine: Engine, limit: int = 10) -> None:
    with Session(engine) as session:
        students = session.exec(select(Student).order_by(Student.id).limit(limit)).all()
        careers = {career.id: career.name for career in session.exec(select(Career)).all()}
        tutors = {tutor.id: tutor.name for tutor in session.exec(select(Tutor)).all()}

        print(
            "code       nombre                          carrera                 "
            "ciclo  gpa  asist  lms  desap  deuda  horas  turno     tutor"
        )
        for student in students:
            features = session.get(StudentFeature, student.pseudo_id)
            assert features is not None
            print(
                f"{student.code:<10} {student.full_name:<30} "
                f"{careers[student.career_id]:<22} {features.cycle:>5} "
                f"{features.gpa_avg:>5.2f} {features.attendance_rate:>6.2f} "
                f"{features.lms_participation:>4.2f} {features.failed_courses:>6} "
                f"{features.tuition_debt_months:>6} {features.weekly_work_hours:>6} "
                f"{features.shift:<9} {tutors[student.tutor_id]}"
            )


def main() -> None:
    summary = seed_database(engine)
    print("Seed completado:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    print_sample(engine)


if __name__ == "__main__":
    main()
