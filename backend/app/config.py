import os

JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
PSEUDO_SECRET = os.getenv("PSEUDO_SECRET", "dev-pseudo-secret")

DEMO_MODE = True
DEMO_BANNER = "Datos de demostración (sintéticos) — no representan estudiantes reales"
INSTITUTION = "Instituto Superior Andino (demo)"
PERIOD = "2026-2"
