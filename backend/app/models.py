from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: str
    password_hash: str
    tutor_id: Optional[int] = Field(default=None, foreign_key="tutors.id")


class Tutor(SQLModel, table=True):
    __tablename__ = "tutors"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Faculty(SQLModel, table=True):
    __tablename__ = "faculties"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class Career(SQLModel, table=True):
    __tablename__ = "careers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    faculty_id: int = Field(foreign_key="faculties.id")


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    full_name: str
    gender: str
    career_id: int = Field(foreign_key="careers.id")
    cycle: int
    tutor_id: int = Field(foreign_key="tutors.id")
    pseudo_id: str = Field(unique=True, index=True)


class StudentFeatureBase(SQLModel):
    gpa_avg: float
    grade_trend: float
    last_exam_grade: float
    failed_courses: int
    attendance_rate: float
    consecutive_absences: int
    lms_participation: float
    late_assignments_rate: float
    tuition_debt_months: int
    scholarship: int
    weekly_work_hours: int
    commute_minutes: int
    family_support: int
    socioemotional_adaptation: int
    shift: str
    cycle: int
    age: int


class StudentFeature(StudentFeatureBase, table=True):
    __tablename__ = "student_features"

    pseudo_id: str = Field(primary_key=True)
    updated_at: datetime = Field(default_factory=utc_now)


class HistoricalCohort(StudentFeatureBase, table=True):
    __tablename__ = "historical_cohort"

    id: Optional[int] = Field(default=None, primary_key=True)
    dropped_out: int


class ModelVersion(SQLModel, table=True):
    __tablename__ = "model_versions"

    id: Optional[int] = Field(default=None, primary_key=True)
    algorithm: str
    trained_at: datetime = Field(default_factory=utc_now)
    n_train: int
    f1: float
    precision: float
    recall: float
    pr_auc: float
    threshold: dict = Field(default_factory=dict, sa_column=Column(JSON))
    feature_importance: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    is_active: bool = False
    data_source: str = "synthetic"


class RiskScore(SQLModel, table=True):
    __tablename__ = "risk_scores"

    student_id: int = Field(primary_key=True, foreign_key="students.id")
    probability: float
    level: str
    main_factor: str
    top_factors: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    model_version_id: int = Field(foreign_key="model_versions.id")
    computed_at: datetime = Field(default_factory=utc_now)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    level: str
    main_factor: str
    reasons: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = "pendiente"
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = None


class Intervention(SQLModel, table=True):
    __tablename__ = "interventions"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id", index=True)
    tutor_id: int = Field(foreign_key="tutors.id")
    type: str
    note: str
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class WeeklySnapshot(SQLModel, table=True):
    __tablename__ = "weekly_snapshots"

    week_index: int = Field(primary_key=True)
    real_dropout_pct: float
    projected_risk_pct: float


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=utc_now)
    source: str
    steps: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    distribution_before: dict = Field(default_factory=dict, sa_column=Column(JSON))
    distribution_after: dict = Field(default_factory=dict, sa_column=Column(JSON))
