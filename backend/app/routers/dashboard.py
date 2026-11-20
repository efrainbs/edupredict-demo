from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_role
from app.models import (
    Alert,
    Career,
    Faculty,
    HistoricalCohort,
    RiskScore,
    Student,
    User,
    WeeklySnapshot,
)
from app.schemas import (
    AlertsSummaryOut,
    AtRiskOut,
    DashboardSummaryOut,
    DashboardTrendOut,
    FacultyOut,
    FacultyRiskOut,
    RiskByFacultyOut,
    TrendWeekOut,
)

router = APIRouter(tags=["dashboard"])

DirectorDep = Annotated[User, Depends(require_role("director"))]


def _check_faculty(session: Session, faculty_id: int | None) -> None:
    if faculty_id is not None and session.get(Faculty, faculty_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facultad no encontrada",
        )


def _students(
    session: Session,
    faculty_id: int | None = None,
) -> list[Student]:
    statement = select(Student)
    if faculty_id is not None:
        statement = statement.join(
            Career, Student.career_id == Career.id
        ).where(Career.faculty_id == faculty_id)
    return list(session.exec(statement).all())


def _scores_for(
    session: Session,
    student_ids: list[int],
) -> dict[int, RiskScore]:
    if not student_ids:
        return {}
    scores = session.exec(
        select(RiskScore).where(RiskScore.student_id.in_(student_ids))
    ).all()
    return {score.student_id: score for score in scores}


@router.get("/faculties", response_model=list[FacultyOut])
def list_faculties(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
) -> list[FacultyOut]:
    faculties = session.exec(select(Faculty).order_by(Faculty.id)).all()
    return [FacultyOut(id=faculty.id, name=faculty.name) for faculty in faculties]


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
def dashboard_summary(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
    faculty_id: Annotated[int | None, Query()] = None,
) -> DashboardSummaryOut:
    _check_faculty(session, faculty_id)
    students = _students(session, faculty_id)
    student_ids = [student.id for student in students]
    scores = _scores_for(session, student_ids)

    high = sum(score.level == "alto" for score in scores.values())
    medium = sum(score.level == "medio" for score in scores.values())
    at_risk = high + medium
    enrollment = len(students)

    pending = 0
    critical = 0
    if student_ids:
        alerts = session.exec(
            select(Alert).where(
                Alert.student_id.in_(student_ids),
                Alert.status == "pendiente",
            )
        ).all()
        pending = len(alerts)
        critical = sum(alert.level == "alto" for alert in alerts)

    labels = session.exec(select(HistoricalCohort.dropped_out)).all()
    dropout_rate = sum(labels) / len(labels) if labels else 0.0

    return DashboardSummaryOut(
        enrollment=enrollment,
        retention_rate=round(1 - dropout_rate, 3),
        at_risk=AtRiskOut(
            count=at_risk,
            pct=round(at_risk / enrollment, 3) if enrollment else 0.0,
            high=high,
            medium=medium,
        ),
        alerts=AlertsSummaryOut(pending=pending, critical=critical),
    )


@router.get("/dashboard/trend", response_model=DashboardTrendOut)
def dashboard_trend(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
    faculty_id: Annotated[int | None, Query()] = None,
) -> DashboardTrendOut:
    _check_faculty(session, faculty_id)
    snapshots = session.exec(
        select(WeeklySnapshot).order_by(WeeklySnapshot.week_index)
    ).all()
    return DashboardTrendOut(
        weeks=[
            TrendWeekOut(
                week=snapshot.week_index,
                real_dropout_pct=snapshot.real_dropout_pct,
                projected_risk_pct=snapshot.projected_risk_pct,
            )
            for snapshot in snapshots
        ]
    )


@router.get("/dashboard/risk-by-faculty", response_model=RiskByFacultyOut)
def dashboard_risk_by_faculty(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
) -> RiskByFacultyOut:
    faculties = session.exec(select(Faculty).order_by(Faculty.id)).all()
    careers = {
        career.id: career for career in session.exec(select(Career)).all()
    }
    students = session.exec(select(Student)).all()
    scores = _scores_for(session, [student.id for student in students])

    counts: dict[int, dict[str, int]] = {
        faculty.id: {"alto": 0, "medio": 0, "bajo": 0} for faculty in faculties
    }
    for student in students:
        career = careers.get(student.career_id)
        if career is None:
            continue
        level = scores.get(student.id).level if student.id in scores else "bajo"
        counts[career.faculty_id][level] += 1

    return RiskByFacultyOut(
        faculties=[
            FacultyRiskOut(
                faculty_id=faculty.id,
                name=faculty.name,
                high=counts[faculty.id]["alto"],
                medium=counts[faculty.id]["medio"],
                low=counts[faculty.id]["bajo"],
            )
            for faculty in faculties
        ]
    )
