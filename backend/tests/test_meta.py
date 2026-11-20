from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meta() -> None:
    response = client.get("/api/meta")

    assert response.status_code == 200
    assert response.json() == {
        "demo_mode": True,
        "banner": "Datos de demostración (sintéticos) — no representan estudiantes reales",
        "institution": "Instituto Superior Andino (demo)",
        "period": "2026-2",
    }
