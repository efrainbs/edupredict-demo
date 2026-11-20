from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

from app.models import (
    Alert,
    ModelVersion,
    RiskScore,
    Student,
    WeeklySnapshot,
)
from app.services.rules import alert_reasons
from ml.features import FEATURE_COLUMNS
from ml.generate_data import seed_database
from ml.train import train_model

CURATED_TARGETS = {
    "Carlos Mendoza Ríos": ("alto", "Bajo rendimiento"),
    "Ana López Silva": ("alto", "Económico / Laboral"),
    "Luis Quispe Mamani": ("medio", "Inasistencias"),
    "Sofía Castro Vega": ("medio", "Socioemocional"),
    "Diego Torres Ruiz": ("bajo", "Ninguno"),
}


@pytest.fixture(scope="module")
def trained_engine(tmp_path_factory):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    seed_database(engine)
    artifacts = tmp_path_factory.mktemp("artifacts")
    summary = train_model(engine, artifacts)
    yield engine, summary
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


def test_model_metrics_and_artifact(trained_engine):
    engine, summary = trained_engine

    assert summary["f1"] >= 0.55
    assert summary["n_train"] == 3200
    assert Path(summary["model_path"]).exists()

    with Session(engine) as session:
        active = session.exec(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).one()

    assert active.algorithm == "XGBoost"
    assert active.n_train == 3200
    assert active.f1 == pytest.approx(summary["f1"])
    assert active.data_source == "synthetic"
    assert set(active.threshold) == {"high", "medium"}
    assert len(active.feature_importance) == 17


def test_risk_distribution(trained_engine):
    engine, _ = trained_engine

    with Session(engine) as session:
        levels = Counter(score.level for score in session.exec(select(RiskScore)).all())

    total = sum(levels.values())
    assert total == 1500
    assert 0.03 <= levels["alto"] / total <= 0.13
    assert 0.12 <= levels["medio"] / total <= 0.22
    assert 0.70 <= levels["bajo"] / total <= 0.80


def test_curated_students_reach_target_levels(trained_engine):
    engine, _ = trained_engine

    with Session(engine) as session:
        students = {
            student.full_name: student
            for student in session.exec(select(Student)).all()
            if student.full_name in CURATED_TARGETS
        }

        for name, (expected_level, expected_factor) in CURATED_TARGETS.items():
            score = session.get(RiskScore, students[name].id)
            assert score is not None
            assert score.level == expected_level
            assert score.main_factor == expected_factor


def test_high_and_medium_have_factors_and_pending_alerts(trained_engine):
    engine, _ = trained_engine

    with Session(engine) as session:
        scores = session.exec(select(RiskScore)).all()
        alerts = session.exec(select(Alert)).all()

    pending = Counter(
        alert.student_id for alert in alerts if alert.status == "pendiente"
    )

    for score in scores:
        if score.level in {"alto", "medio"}:
            assert len(score.top_factors) == 3
            assert all(factor["text"] for factor in score.top_factors)
            assert all(factor["impact"] > 0 for factor in score.top_factors)
            assert pending[score.student_id] == 1
        else:
            assert score.top_factors == []
            assert pending[score.student_id] == 0

    for alert in alerts:
        assert len(alert.reasons) <= 2
        assert alert.level in {"alto", "medio"}


def test_model_uses_only_allowed_features(trained_engine):
    engine, _ = trained_engine

    with Session(engine) as session:
        active = session.exec(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).one()

    features = {item["feature"] for item in active.feature_importance}

    assert features == set(FEATURE_COLUMNS)
    assert "gender" not in features
    assert not any(
        forbidden in feature
        for feature in features
        for forbidden in ("dropout", "retiro", "abandono")
    )


def test_week_eight_snapshot_matches_live_risk(trained_engine):
    engine, _ = trained_engine

    with Session(engine) as session:
        scores = session.exec(select(RiskScore)).all()
        snapshot = session.get(WeeklySnapshot, 8)

    at_risk = sum(score.level in {"alto", "medio"} for score in scores)
    expected = round(at_risk / len(scores) * 100, 1)

    assert snapshot is not None
    assert snapshot.projected_risk_pct == expected


def test_alert_rules_order_and_limit():
    row = SimpleNamespace(
        consecutive_absences=4,
        last_exam_grade=9.0,
        tuition_debt_months=2,
        lms_participation=0.20,
        grade_trend=-3.0,
    )

    assert alert_reasons(row) == [
        "4 inasistencias consecutivas",
        "Nota de parcial: 9.0/20",
    ]

    clean = SimpleNamespace(
        consecutive_absences=0,
        last_exam_grade=15.0,
        tuition_debt_months=0,
        lms_participation=0.80,
        grade_trend=0.5,
    )

    assert alert_reasons(clean) == []
