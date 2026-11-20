from pydantic import BaseModel


class MetaResponse(BaseModel):
    demo_mode: bool
    banner: str
    institution: str
    period: str
