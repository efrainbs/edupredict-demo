import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app

output = ROOT.parent / "frontend" / "src" / "api" / "openapi.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
