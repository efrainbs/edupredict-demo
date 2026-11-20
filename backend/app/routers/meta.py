from fastapi import APIRouter

from app import config
from app.schemas import MetaResponse

router = APIRouter(tags=["meta"])


@router.get("/meta", response_model=MetaResponse)
def read_meta() -> MetaResponse:
    return MetaResponse(
        demo_mode=config.DEMO_MODE,
        banner=config.DEMO_BANNER,
        institution=config.INSTITUTION,
        period=config.PERIOD,
    )
