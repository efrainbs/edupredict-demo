import csv
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

from app.db import get_session
from app.main import app
from app.models import Alert, ModelVersion, RiskScore, Student, StudentFeature
from app.services.pseudonymize import pseudo_id_for
from ml.generate_data import seed_database
from ml.train import train_model

HEADER = [
    "codigo_estudiante",
    "nombre_completo",
    "genero",
    "carrera",
    "ciclo",
    "tutor",
    "promedio_general",
    "tendencia_notas",
    "nota_ultimo_examen",
    "cursos_desaprobados",
    "tasa_asistencia",
    "inasistencias_consecutivas",
    "participacion_lms",
    "tasa_entregas_tardias",
    "meses_deuda_matricula",
    "beca",
    "horas_trabajo_semanal",
    "minutos_translado",
    "apoyo_familiar",
    "adaptacion_socioemocional",
    "turno",
    "edad",
]


@pytest.fixture(scope="module")
def upload_engine(tmp_path_factory):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    seed_database(engine)
    train_model(engine, tmp_path_factory.mktemp("upload-artifacts"))
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="module")
def client(upload_engine):
    def override_get_session():
        with Session(upload_engine) as session:
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


def _csv(rows: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADER)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _row(
    code: str,
    name: str,
    *,
    gender: str = "F",
    career: str = "Administración",
    cycle: int = 2,
    tutor: str = "Roberto Díaz",
    gpa: float = 18.0,
    trend: float = 2.0,
    exam: float = 18.0,
    failed: int = 0,
    attendance: float = 0.98,
    absences: int = 0,
    lms: float = 0.90,
    late: float = 0.05,
    debt: int = 0,
    scholarship: int = 1,
    work: int = 0,
    commute: int = 20,
    family: int = 5,
    adaptation: int = 5,
    shift: str = "diurno",
    age: int = 20,
) -> dict:
    return {
        "codigo_estudiante": code,
        "nombre_completo": name,
        "genero": gender,
        "carrera": career,
        "ciclo": cycle,
        "tutor": tutor,
        "promedio_general": gpa,
        "tendencia_notas": trend,
        "nota_ultimo_examen": exam,
        "cursos_desaprobados": failed,
        "tasa_asistencia": attendance,
        "inasistencias_consecutivas": absences,
        "participacion_lms": lms,
        "tasa_entregas_tardias": late,
        "meses_deuda_matricula": debt,
        "beca": scholarship,
        "horas_trabajo_semanal": work,
        "minutos_translado": commute,
        "apoyo_familiar": family,
        "adaptacion_socioemocional": adaptation,
        "turno": shift,
        "edad": age,
    }


def test_template_csv(client, director_headers, tutor_headers):
    response = client.get("/api/upload/template.csv", headers=director_headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines()[0].split(",") == HEADER
    assert len(response.text.strip().splitlines()) == 3

    assert (
        client.get("/api/upload/template.csv", headers=tutor_headers).status_code
        == 403
    )
    assert client.get("/api/upload/template.csv").status_code == 401


def test_upload_processes_valid_rows_and_reports_errors(
    client, director_headers, tutor_headers, upload_engine
):
    new_code = "U00999999"
    invalid_code = "U00999998"
    content = _csv(
        [
            _row("U00000001", "Carlos Mendoza Ríos", career="Ing. de Software", cycle=3),
            _row(new_code, "Estudiante Nuevo Prueba", career="Administración"),
            _row(invalid_code, "Fila Inválida", attendance=1.4),
        ]
    )

    response = client.post(
        "/api/upload",
        headers=director_headers,
        files={"file": ("demo.csv", content, "text/csv")},
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert isinstance(body["run_id"], int)
    assert [step["key"] for step in body["steps"]] == [
        "ingest",
        "clean",
        "pseudonymize",
        "score",
        "alerts",
    ]
    assert body["steps"][0]["detail"] == "3 filas recibidas"
    assert body["steps"][1]["detail"] == "2 válidas, 1 rechazadas"
    assert body["steps"][2]["detail"].startswith("2 identificadores")
    assert body["steps"][3]["detail"].startswith("2 estudiantes")

    assert len(body["errors"]) == 1
    assert body["errors"][0]["row"] == 4
    assert body["errors"][0]["column"] == "tasa_asistencia"
    assert "rango" in body["errors"][0]["reason"]

    assert sum(body["distribution_before"].values()) == 1500
    assert sum(body["distribution_after"].values()) == 1501

    assert len(body["model_view_sample"]) == 3
    for row in body["model_view_sample"]:
        assert "pseudo_id" in row
        assert "full_name" not in row
        assert "student_code" not in row

    with Session(upload_engine) as session:
        active = session.exec(
            select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
        ).one()
        assert set(active.threshold) == {"high", "medium"}

        carlos = session.exec(
            select(Student).where(Student.code == "U00000001")
        ).one()
        carlos_score = session.get(RiskScore, carlos.id)
        assert carlos_score is not None
        assert carlos_score.level == "bajo"
        carlos_alerts = session.exec(
            select(Alert).where(Alert.student_id == carlos.id)
        ).all()
        assert carlos_alerts
        assert all(alert.status == "cerrada" for alert in carlos_alerts)
        assert all(alert.resolved_at is not None for alert in carlos_alerts)

        untouched = session.exec(
            select(Student).where(Student.code == "U00000002")
        ).one()
        assert session.get(RiskScore, untouched.id) is not None

        new_student = session.exec(
            select(Student).where(Student.code == new_code)
        ).one()
        assert new_student.pseudo_id == pseudo_id_for(new_code)
        assert session.get(StudentFeature, new_student.pseudo_id) is not None
        assert session.get(RiskScore, new_student.id) is not None

        invalid_student = session.exec(
            select(Student).where(Student.code == invalid_code)
        ).first()
        assert invalid_student is None

    assert (
        client.post(
            "/api/upload",
            headers=tutor_headers,
            files={"file": ("demo.csv", content, "text/csv")},
        ).status_code
        == 403
    )


def test_upload_rejects_invalid_file_shapes(client, director_headers):
    missing_columns = b"student_code,full_name\nU00000001,Prueba\n"
    response = client.post(
        "/api/upload",
        headers=director_headers,
        files={"file": ("demo.csv", missing_columns, "text/csv")},
    )
    assert response.status_code == 422
    assert "columnas obligatorias" in response.json()["detail"]

    response = client.post(
        "/api/upload",
        headers=director_headers,
        files={"file": ("demo.txt", b"hola", "text/plain")},
    )
    assert response.status_code == 422
