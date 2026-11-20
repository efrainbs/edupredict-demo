import hashlib
import hmac

from app.config import PSEUDO_SECRET


def pseudo_id_for(student_code: str) -> str:
    digest = hmac.new(
        PSEUDO_SECRET.encode("utf-8"),
        student_code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:16]
