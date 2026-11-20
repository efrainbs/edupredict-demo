from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_owned_student, require_role
from app.models import Alert, Intervention, Student, Tutor, User
from app.schemas import InterventionCreate, InterventionOut

router = APIRouter(tags=["interventions"])


def _tutor_names(session: Session) -> dict[int, str]:
    names = {
        user.tutor_id: user.name
        for user in session.exec(
            select(User).where(User.role == "tutor", User.tutor_id != None)  # noqa: E711
        ).all()
    }
    for tutor in session.exec(select(Tutor)).all():
        names.setdefault(tutor.id, tutor.name)
    return names


def _intervention_out(
    intervention: Intervention,
    tutor_name: str,
) -> InterventionOut:
    return InterventionOut(
        id=intervention.id,
        type=intervention.type,
        note=intervention.note,
        scheduled_at=intervention.scheduled_at,
        created_at=intervention.created_at,
        tutor_name=tutor_name,
    )


def interventions_for_student(
    session: Session,
    student_id: int,
) -> list[InterventionOut]:
    interventions = session.exec(
        select(Intervention)
        .where(Intervention.student_id == student_id)
        .order_by(Intervention.created_at.desc(), Intervention.id.desc())
    ).all()
    names = _tutor_names(session)
    return [
        _intervention_out(
            intervention,
            names.get(intervention.tutor_id, "Tutor"),
        )
        for intervention in interventions
    ]


@router.get(
    "/students/{student_id}/interventions",
    response_model=list[InterventionOut],
)
def list_interventions(
    student: Annotated[Student, Depends(get_owned_student)],
    session: Annotated[Session, Depends(get_session)],
) -> list[InterventionOut]:
    return interventions_for_student(session, student.id)


@router.post(
    "/students/{student_id}/interventions",
    response_model=InterventionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_intervention(
    payload: InterventionCreate,
    student: Annotated[Student, Depends(get_owned_student)],
    user: Annotated[User, Depends(require_role("tutor"))],
    session: Annotated[Session, Depends(get_session)],
) -> InterventionOut:
    now = datetime.now(timezone.utc)
    scheduled_at = payload.scheduled_at

    if payload.type == "reunion":
        if scheduled_at is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="La fecha de la reunión es obligatoria",
            )
        if scheduled_at.tzinfo is None:
            scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
        if scheduled_at <= now:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="La reunión debe programarse en el futuro",
            )
    elif scheduled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="scheduled_at solo aplica a reuniones",
        )

    intervention = Intervention(
        student_id=student.id,
        tutor_id=user.tutor_id,
        type=payload.type,
        note=payload.note,
        scheduled_at=scheduled_at,
    )
    session.add(intervention)

    pending_alerts = session.exec(
        select(Alert).where(
            Alert.student_id == student.id,
            Alert.status == "pendiente",
        )
    ).all()
    for alert in pending_alerts:
        alert.status = "atendida"
        alert.resolved_at = now
        session.add(alert)

    session.commit()
    session.refresh(intervention)

    return _intervention_out(intervention, user.name)
