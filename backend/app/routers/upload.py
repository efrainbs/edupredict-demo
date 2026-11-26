from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlmodel import Session

from app.db import get_session
from app.deps import require_role
from app.models import User
from app.schemas import UploadResultOut
from app.services.pipeline import (
    MAX_UPLOAD_BYTES,
    CSV_COLUMNS_ES,
    CsvValidationError,
    ModelUnavailableError,
    process_upload,
)

router = APIRouter(tags=["upload"])

DirectorDep = Annotated[User, Depends(require_role("director"))]

TEMPLATE_HEADER = ",".join(CSV_COLUMNS_ES)

TEMPLATE_ROWS = [
    (
        "U00900001,Estudiante Ejemplo Uno,F,Ing. de Software,2,Roberto Díaz,"
        "14.50,0.50,15.00,0,0.92,0,0.70,0.10,0,1,8,35,4,4,diurno,19"
    ),
    (
        "U00900002,Estudiante Ejemplo Dos,M,Administración,3,Roberto Díaz,"
        "11.20,-1.50,10.00,2,0.74,3,0.35,0.40,2,0,24,70,3,2,nocturno,23"
    ),
]

TEMPLATE_CSV = "\n".join([TEMPLATE_HEADER, *TEMPLATE_ROWS]) + "\n"


@router.get("/upload/template.csv")
def upload_template(_user: DirectorDep) -> Response:
    return Response(
        content=TEMPLATE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="edupredict_template.csv"'
        },
    )


@router.post("/upload", response_model=UploadResultOut)
async def upload_students(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
) -> UploadResultOut:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe tener extensión .csv",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo supera el límite de 5 MB",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe estar codificado en UTF-8",
        ) from None

    try:
        result = process_upload(session, text)
    except CsvValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from None
    except ModelUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from None

    return UploadResultOut(**result)
