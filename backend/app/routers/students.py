import unicodedata
from collections import defaultdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_owned_student, require_role
from app.models import (
    Alert,
    Career,
    Faculty,
    Intervention,
    RiskScore,
    Student,
    StudentFeature,
    User,
)
from app.routers.interventions import interventions_for_student
from app.schemas import (
    IndicatorsOut,
    RiskDetailOut,
    RiskLevel,
    StudentDetailOut,
    StudentListItemOut,
    TopFactorOut,
    TutorSummaryOut,
)

router = APIRouter(tags=["students"])

TutorDep = Annotated[User, Depends(require_role("tutor"))]

LEVEL_ORDER = {"alto": 0, "medio": 1, "bajo": 2}
RISK_DISCLAIMER = (
    "Esta alerta es una señal para ofrecer acompañamiento oportuno. "
    "No es una etiqueta definitiva ni genera ninguna sanción automática."
)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def _tutor_students(session: Session, user: User) -> list[Student]:
    if user.tutor_id is None:
        return []
    return list(
        session.exec(
            select(Student)
            .where(Student.tutor_id == user.tutor_id)
            .order_by(Student.id)
        ).all()
    )


@router.get("/tutor/summary", response_model=TutorSummaryOut)
def tutor_summary(
    user: TutorDep,
    session: Annotated[Session, Depends(get_session)],
) -> TutorSummaryOut:
    students = _tutor_students(session, user)
    student_ids = [student.id for student in students]

    scores = {}
    if student_ids:
        scores = {
            score.student_id: score
            for score in session.exec(
                select(RiskScore).where(RiskScore.student_id.in_(student_ids))
            ).all()
        }

    in_observation = sum(
        score.level in {"alto", "medio"} for score in scores.values()
    )

    critical_pending = 0
    if student_ids:
        alerts = session.exec(
            select(Alert).where(
                Alert.student_id.in_(student_ids),
                Alert.status == "pendiente",
                Alert.level == "alto",
            )
        ).all()
        critical_pending = len(alerts)

    return TutorSummaryOut(
        tutor_name=user.name,
        in_observation=in_observation,
        critical_pending=critical_pending,
    )


@router.get("/students", response_model=list[StudentListItemOut])
def list_students(
    user: TutorDep,
    session: Annotated[Session, Depends(get_session)],
    risk: Annotated[RiskLevel | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> list[StudentListItemOut]:
    students = _tutor_students(session, user)
    if not students:
        return []

    student_ids = [student.id for student in students]
    scores = {
        score.student_id: score
        for score in session.exec(
            select(RiskScore).where(RiskScore.student_id.in_(student_ids))
        ).all()
    }
    careers = {
        career.id: career for career in session.exec(select(Career)).all()
    }

    pending_by_student: dict[int, list[Alert]] = defaultdict(list)
    for alert in session.exec(
        select(Alert)
        .where(
            Alert.student_id.in_(student_ids),
            Alert.status == "pendiente",
        )
        .order_by(Alert.created_at, Alert.id)
    ).all():
        pending_by_student[alert.student_id].append(alert)

    last_contact: dict[int, datetime] = {}
    for intervention in session.exec(
        select(Intervention).where(Intervention.student_id.in_(student_ids))
    ).all():
        current = last_contact.get(intervention.student_id)
        if current is None or intervention.created_at > current:
            last_contact[intervention.student_id] = intervention.created_at

    query = _normalize(q) if q else None
    items: list[StudentListItemOut] = []

    for student in students:
        score = scores.get(student.id)
        level = score.level if score else "bajo"
        probability = score.probability if score else 0.0

        if risk is not None and level != risk:
            continue
        if query is not None and query not in _normalize(
            f"{student.full_name} {student.code}"
        ):
            continue

        alerts = pending_by_student.get(student.id, [])
        career = careers.get(student.career_id)
        items.append(
            StudentListItemOut(
                id=student.id,
                code=student.code,
                full_name=student.full_name,
                career=career.name if career else "",
                cycle=student.cycle,
                risk_level=level,
                probability=probability,
                main_factor=score.main_factor if score else "Ninguno",
                reasons=alerts[-1].reasons if alerts else [],
                pending_alerts=len(alerts),
                last_contact_at=last_contact.get(student.id),
            )
        )

    items.sort(
        key=lambda item: (LEVEL_ORDER[item.risk_level], -item.probability)
    )
    return items


@router.get("/students/{student_id}", response_model=StudentDetailOut)
def student_detail(
    student: Annotated[Student, Depends(get_owned_student)],
    session: Annotated[Session, Depends(get_session)],
) -> StudentDetailOut:
    score = session.get(RiskScore, student.id)
    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El estudiante no tiene puntuación de riesgo",
        )

    career = session.get(Career, student.career_id)
    faculty = session.get(Faculty, career.faculty_id) if career else None
    features = session.get(StudentFeature, student.pseudo_id)
    if career is None or faculty is None or features is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron los datos del estudiante",
        )

    return StudentDetailOut(
        id=student.id,
        code=student.code,
        full_name=student.full_name,
        career=career.name,
        faculty=faculty.name,
        cycle=student.cycle,
        risk=RiskDetailOut(
            level=score.level,
            probability=score.probability,
            score=round(score.probability * 100),
            main_factor=score.main_factor,
            computed_at=score.computed_at,
            top_factors=[
                TopFactorOut(**factor) for factor in score.top_factors
            ],
            disclaimer=RISK_DISCLAIMER,
        ),
        indicators=IndicatorsOut(
            gpa_avg=features.gpa_avg,
            attendance_rate=features.attendance_rate,
            lms_participation=features.lms_participation,
            tuition_debt_months=features.tuition_debt_months,
            weekly_work_hours=features.weekly_work_hours,
            family_support=features.family_support,
            socioemotional_adaptation=features.socioemotional_adaptation,
        ),
        interventions=interventions_for_student(session, student.id),
    )
