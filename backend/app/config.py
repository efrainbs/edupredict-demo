import os
from pathlib import Path

JWT_SECRET = os.getenv(
    "JWT_SECRET", "dev-jwt-secret-change-me-32-bytes-min"
)
PSEUDO_SECRET = os.getenv("PSEUDO_SECRET", "dev-pseudo-secret")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "edupredict.db"

DEMO_MODE = True
DEMO_BANNER = "Datos de demostración (sintéticos) — no representan estudiantes reales"
INSTITUTION = "Instituto Superior Andino (demo)"
PERIOD = "2026-2"

RISK_HIGH_PERCENTILE = 92
RISK_MEDIUM_PERCENTILE = 75
