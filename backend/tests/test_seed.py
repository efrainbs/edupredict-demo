from collections import Counter

import bcrypt
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

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
from ml.generate_data import FEATURE_NAMES, seed_database


def _in_memory_engine():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="module")
def seeded_engine():
    engine = _in_memory_engine()
    seed_database(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


def test_seed_counts(seeded_engine):
    with Session(seeded_engine) as session:
        assert len(session.exec(select(Faculty)).all()) == 4
        assert len(session.exec(select(Career)).all()) == 8
        assert len(session.exec(select(Tutor)).all()) == 20
        assert len(session.exec(select(Student)).all()) == 1500
        assert len(session.exec(select(StudentFeature)).all()) == 1500
        assert len(session.exec(select(HistoricalCohort)).all()) == 4000
        assert len(session.exec(select(User)).all()) == 3
        assert len(session.exec(select(WeeklySnapshot)).all()) == 8


def test_each_tutor_has_between_50_and_100_students(seeded_engine):
    with Session(seeded_engine) as session:
        students = session.exec(select(Student)).all()

    counts = Counter(student.tutor_id for student in students)

    assert len(counts) == 20
    assert all(50 <= count <= 100 for count in counts.values())


def test_historical_dropout_prevalence(seeded_engine):
    with Session(seeded_engine) as session:
        labels = session.exec(select(HistoricalCohort.dropped_out)).all()

    prevalence = sum(labels) / len(labels)

    assert 0.15 <= prevalence <= 0.20


def test_pseudonymization_has_no_identity_columns(seeded_engine):
    student_feature_columns = {
        column["name"] for column in inspect(seeded_engine).get_columns("student_features")
    }
    historical_columns = {
        column["name"] for column in inspect(seeded_engine).get_columns("historical_cohort")
    }

    assert set(FEATURE_NAMES).issubset(student_feature_columns)
    assert {"full_name", "code", "gender"}.isdisjoint(student_feature_columns)
    assert "pseudo_id" not in historical_columns
    assert {"full_name", "code", "gender"}.isdisjoint(historical_columns)


def test_pseudonymization_is_deterministic_and_consistent(seeded_engine):
    with Session(seeded_engine) as session:
        students = session.exec(select(Student)).all()
        features = session.exec(select(StudentFeature)).all()

    assert pseudo_id_for("U00000001") == pseudo_id_for("U00000001")
    assert {student.pseudo_id for student in students} == {
        feature.pseudo_id for feature in features
    }
    assert all(student.pseudo_id == pseudo_id_for(student.code) for student in students)
    assert all(feature.shift in {"diurno", "nocturno"} for feature in features)


def test_feature_ranges(seeded_engine):
    with Session(seeded_engine) as session:
        current = session.exec(select(StudentFeature)).all()
        historical = session.exec(select(HistoricalCohort)).all()

    for row in [*current, *historical]:
        assert 0 <= row.gpa_avg <= 20
        assert -5 <= row.grade_trend <= 5
        assert 0 <= row.last_exam_grade <= 20
        assert 0 <= row.failed_courses <= 6
        assert 0 <= row.attendance_rate <= 1
        assert 0 <= row.consecutive_absences <= 10
        assert 0 <= row.lms_participation <= 1
        assert 0 <= row.late_assignments_rate <= 1
        assert 0 <= row.tuition_debt_months <= 4
        assert row.scholarship in {0, 1}
        assert 0 <= row.weekly_work_hours <= 48
        assert 5 <= row.commute_minutes <= 150
        assert 1 <= row.family_support <= 5
        assert 1 <= row.socioemotional_adaptation <= 5
        assert row.shift in {"diurno", "nocturno"}
        assert 1 <= row.cycle <= 6
        assert 17 <= row.age <= 40


def test_curated_students_belong_to_tutor_one(seeded_engine):
    curated = {
        "Carlos Mendoza Ríos": "Ing. de Software",
        "Ana López Silva": "Administración",
        "Luis Quispe Mamani": "Ing. Industrial",
        "Sofía Castro Vega": "Enfermería",
        "Diego Torres Ruiz": "Diseño Gráfico",
    }

    with Session(seeded_engine) as session:
        tutor_one = session.exec(select(Tutor).where(Tutor.name == "Roberto Díaz")).one()
        careers = {career.name: career.id for career in session.exec(select(Career)).all()}
        students = {
            student.full_name: student
            for student in session.exec(select(Student)).all()
            if student.full_name in curated
        }

    for name, career_name in curated.items():
        student = students[name]
        assert student.tutor_id == tutor_one.id
        assert student.career_id == careers[career_name]


def test_demo_users(seeded_engine):
    with Session(seeded_engine) as session:
        users = {user.email: user for user in session.exec(select(User)).all()}
        tutors = {tutor.name: tutor.id for tutor in session.exec(select(Tutor)).all()}

    assert set(users) == {
        "director@edupredict.demo",
        "tutor1@edupredict.demo",
        "tutor2@edupredict.demo",
    }
    assert users["director@edupredict.demo"].role == "director"
    assert users["director@edupredict.demo"].tutor_id is None
    assert users["tutor1@edupredict.demo"].role == "tutor"
    assert users["tutor1@edupredict.demo"].tutor_id == tutors["Roberto Díaz"]
    assert users["tutor2@edupredict.demo"].tutor_id == tutors["Mariela Salazar"]
    assert all(
        bcrypt.checkpw(b"demo1234", user.password_hash.encode("utf-8"))
        for user in users.values()
    )


def test_seed_is_idempotent():
    engine = _in_memory_engine()
    try:
        seed_database(engine)
        seed_database(engine)

        with Session(engine) as session:
            assert len(session.exec(select(Student)).all()) == 1500
            assert len(session.exec(select(StudentFeature)).all()) == 1500
            assert len(session.exec(select(HistoricalCohort)).all()) == 4000
    finally:
        SQLModel.metadata.drop_all(engine)
        engine.dispose()
