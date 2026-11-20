from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

from app.db import get_session
from app.main import app
from app.models import Alert, RiskScore, Student, User
from ml.generate_data import seed_database
from ml.train import train_model

RISK_DISCLAIMER = (
    "Esta alerta es una señal para ofrecer acompañamiento oportuno. "
    "No es una etiqueta definitiva ni genera ninguna sanción automática."
)


@pytest.fixture(scope="module")
def api_engine(tmp_path_factory):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    seed_database(engine)
    artifacts = tmp_path_factory.mktemp("api-artifacts")
    train_model(engine, artifacts)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def client(api_engine):
    def override_get_session():
        with Session(api_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="module")
def director_headers(client):
    return _login(client, "director@edupredict.demo")


@pytest.fixture(scope="module")
def tutor_headers(client):
    return _login(client, "tutor1@edupredict.demo")


def _student_id(engine, full_name: str) -> int:
    with Session(engine) as session:
        return session.exec(
            select(Student.id).where(Student.full_name == full_name)
        ).one()


def _other_tutor_student_id(engine) -> int:
    with Session(engine) as session:
        tutor = session.exec(
            select(User).where(User.email == "tutor2@edupredict.demo")
        ).one()
        return session.exec(
            select(Student.id).where(Student.tutor_id == tutor.tutor_id)
        ).first()


def test_auth_login_and_me(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "tutor1@edupredict.demo", "password": "demo1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {
        "id": 2,
        "name": "Prof. Roberto Díaz",
        "role": "tutor",
        "tutor_id": 1,
    }

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json() == body["user"]

    bad = client.post(
        "/api/auth/login",
        json={"email": "tutor1@edupredict.demo", "password": "incorrecta"},
    )
    assert bad.status_code == 401


def test_auth_is_required(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/dashboard/summary").status_code == 401
    assert (
        client.get(
            "/api/students",
            headers={"Authorization": "Bearer not-a-token"},
        ).status_code
        == 401
    )


def test_role_access_is_enforced(client, director_headers, tutor_headers):
    assert (
        client.get("/api/dashboard/summary", headers=tutor_headers).status_code
        == 403
    )
    assert client.get("/api/faculties", headers=tutor_headers).status_code == 403
    assert client.get("/api/model/info", headers=tutor_headers).status_code == 403
    assert client.get("/api/students", headers=director_headers).status_code == 403
    assert (
        client.get("/api/tutor/summary", headers=director_headers).status_code
        == 403
    )


def test_director_dashboard_endpoints(client, director_headers, api_engine):
    faculties = client.get("/api/faculties", headers=director_headers)
    assert faculties.status_code == 200
    assert len(faculties.json()) == 4
    assert set(faculties.json()[0]) == {"id", "name"}

    summary = client.get("/api/dashboard/summary", headers=director_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert set(body) == {"enrollment", "retention_rate", "at_risk", "alerts"}
    assert body["enrollment"] == 1500
    assert body["at_risk"] == {
        "count": 375,
        "pct": 0.25,
        "high": 120,
        "medium": 255,
    }
    assert body["alerts"] == {"pending": 375, "critical": 120}
    assert 0.15 <= 1 - body["retention_rate"] <= 0.20

    filtered = client.get(
        "/api/dashboard/summary",
        headers=director_headers,
        params={"faculty_id": 1},
    )
    assert filtered.status_code == 200
    assert filtered.json()["enrollment"] < 1500
    assert filtered.json()["at_risk"]["count"] <= 375

    trend = client.get("/api/dashboard/trend", headers=director_headers)
    assert trend.status_code == 200
    assert len(trend.json()["weeks"]) == 8
    assert set(trend.json()["weeks"][0]) == {
        "week",
        "real_dropout_pct",
        "projected_risk_pct",
    }

    by_faculty = client.get(
        "/api/dashboard/risk-by-faculty", headers=director_headers
    )
    assert by_faculty.status_code == 200
    rows = by_faculty.json()["faculties"]
    assert len(rows) == 4
    assert sum(row["high"] + row["medium"] + row["low"] for row in rows) == 1500
    assert sum(row["high"] for row in rows) == 120
    assert sum(row["medium"] for row in rows) == 255


def test_director_model_info(client, director_headers):
    response = client.get("/api/model/info", headers=director_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "XGBoost"
    assert body["n_train"] == 3200
    assert body["data_source"] == "synthetic"
    assert body["disclaimer"] == (
        "Métricas sobre datos sintéticos — no son evidencia de desempeño real"
    )
    assert set(body["metrics"]) == {"f1", "precision", "recall", "pr_auc"}
    assert len(body["feature_importance"]) == 10
    assert all(item["label"] for item in body["feature_importance"])


def test_tutor_summary_and_students(client, tutor_headers, api_engine):
    summary = client.get("/api/tutor/summary", headers=tutor_headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["tutor_name"] == "Prof. Roberto Díaz"
    assert isinstance(body["in_observation"], int)
    assert isinstance(body["critical_pending"], int)

    with Session(api_engine) as session:
        tutor = session.exec(
            select(User).where(User.email == "tutor1@edupredict.demo")
        ).one()
        own_ids = {
            student.id
            for student in session.exec(
                select(Student).where(Student.tutor_id == tutor.tutor_id)
            ).all()
        }
        own_scores = session.exec(
            select(RiskScore).where(RiskScore.student_id.in_(own_ids))
        ).all()
        pending = session.exec(
            select(Alert).where(
                Alert.student_id.in_(own_ids),
                Alert.status == "pendiente",
                Alert.level == "alto",
            )
        ).all()

    assert body["in_observation"] == sum(
        score.level in {"alto", "medio"} for score in own_scores
    )
    assert body["critical_pending"] == len(pending)

    students = client.get("/api/students", headers=tutor_headers)
    assert students.status_code == 200
    rows = students.json()
    assert rows
    assert len(rows) <= 100
    assert {row["id"] for row in rows}.issubset(own_ids)
    assert set(rows[0]) == {
        "id",
        "code",
        "full_name",
        "career",
        "cycle",
        "risk_level",
        "probability",
        "main_factor",
        "reasons",
        "pending_alerts",
        "last_contact_at",
    }

    order = {"alto": 0, "medio": 1, "bajo": 2}
    assert rows == sorted(
        rows,
        key=lambda row: (order[row["risk_level"]], -row["probability"]),
    )


def test_student_search_ignores_accents(client, tutor_headers):
    response = client.get(
        "/api/students",
        headers=tutor_headers,
        params={"risk": "alto", "q": "mendoza"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["full_name"] == "Carlos Mendoza Ríos"
    assert rows[0]["risk_level"] == "alto"

    accented = client.get(
        "/api/students",
        headers=tutor_headers,
        params={"risk": "medio", "q": "sofia"},
    )
    assert accented.status_code == 200
    assert len(accented.json()) == 1
    assert accented.json()[0]["full_name"] == "Sofía Castro Vega"

    invalid = client.get(
        "/api/students",
        headers=tutor_headers,
        params={"risk": "critico"},
    )
    assert invalid.status_code == 422


def test_student_detail(client, tutor_headers, api_engine):
    student_id = _student_id(api_engine, "Carlos Mendoza Ríos")
    response = client.get(
        f"/api/students/{student_id}", headers=tutor_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Carlos Mendoza Ríos"
    assert body["career"] == "Ing. de Software"
    assert body["faculty"] == "Ingeniería"
    assert body["risk"]["level"] == "alto"
    assert body["risk"]["score"] == round(body["risk"]["probability"] * 100)
    assert body["risk"]["main_factor"] == "Bajo rendimiento"
    assert body["risk"]["disclaimer"] == RISK_DISCLAIMER
    assert len(body["risk"]["top_factors"]) == 3
    assert set(body["indicators"]) == {
        "gpa_avg",
        "attendance_rate",
        "lms_participation",
        "tuition_debt_months",
        "weekly_work_hours",
        "family_support",
        "socioemotional_adaptation",
    }
    assert body["interventions"] == []

    missing = client.get("/api/students/999999", headers=tutor_headers)
    assert missing.status_code == 404


def test_tutor_cannot_access_other_tutor_student(
    client, tutor_headers, api_engine
):
    other_id = _other_tutor_student_id(api_engine)

    assert (
        client.get(
            f"/api/students/{other_id}", headers=tutor_headers
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/students/{other_id}/interventions", headers=tutor_headers
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/students/{other_id}/interventions",
            headers=tutor_headers,
            json={"type": "seguimiento", "note": "Intento no autorizado"},
        ).status_code
        == 403
    )


def test_past_reunion_is_rejected(client, tutor_headers, api_engine):
    student_id = _student_id(api_engine, "Carlos Mendoza Ríos")
    past = datetime.now(timezone.utc) - timedelta(days=1)

    response = client.post(
        f"/api/students/{student_id}/interventions",
        headers=tutor_headers,
        json={
            "type": "reunion",
            "note": "Reunión atrasada",
            "scheduled_at": past.isoformat(),
        },
    )
    assert response.status_code == 422


def test_intervention_attends_pending_alerts(
    client, tutor_headers, api_engine
):
    student_id = _student_id(api_engine, "Carlos Mendoza Ríos")
    before = client.get("/api/tutor/summary", headers=tutor_headers).json()

    response = client.post(
        f"/api/students/{student_id}/interventions",
        headers=tutor_headers,
        json={
            "type": "seguimiento",
            "note": "Llamé al estudiante para coordinar acompañamiento.",
            "scheduled_at": None,
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["type"] == "seguimiento"
    assert created["note"] == (
        "Llamé al estudiante para coordinar acompañamiento."
    )
    assert created["tutor_name"] == "Prof. Roberto Díaz"
    assert created["scheduled_at"] is None

    listed = client.get(
        f"/api/students/{student_id}/interventions", headers=tutor_headers
    )
    assert listed.status_code == 200
    assert listed.json()[0] == created

    with Session(api_engine) as session:
        alerts = session.exec(
            select(Alert).where(Alert.student_id == student_id)
        ).all()
    assert alerts
    assert all(alert.status == "atendida" for alert in alerts)
    assert all(alert.resolved_at is not None for alert in alerts)

    after = client.get("/api/tutor/summary", headers=tutor_headers).json()
    assert after["critical_pending"] == before["critical_pending"] - 1
