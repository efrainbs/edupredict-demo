from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["alto", "medio", "bajo"]
InterventionType = Literal["seguimiento", "reunion", "mensaje"]


class MetaResponse(BaseModel):
    demo_mode: bool
    banner: str
    institution: str
    period: str


class UserOut(BaseModel):
    id: int
    name: str
    role: str
    tutor_id: int | None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class FacultyOut(BaseModel):
    id: int
    name: str


class AtRiskOut(BaseModel):
    count: int
    pct: float
    high: int
    medium: int


class AlertsSummaryOut(BaseModel):
    pending: int
    critical: int


class DashboardSummaryOut(BaseModel):
    enrollment: int
    retention_rate: float
    at_risk: AtRiskOut
    alerts: AlertsSummaryOut


class TrendWeekOut(BaseModel):
    week: int
    real_dropout_pct: float
    projected_risk_pct: float


class DashboardTrendOut(BaseModel):
    weeks: list[TrendWeekOut]


class FacultyRiskOut(BaseModel):
    faculty_id: int
    name: str
    high: int
    medium: int
    low: int


class RiskByFacultyOut(BaseModel):
    faculties: list[FacultyRiskOut]


class ModelMetricsOut(BaseModel):
    f1: float
    precision: float
    recall: float
    pr_auc: float


class FeatureImportanceOut(BaseModel):
    feature: str
    label: str
    importance: float


class ModelInfoOut(BaseModel):
    algorithm: str
    trained_at: datetime
    n_train: int
    metrics: ModelMetricsOut
    data_source: str
    disclaimer: str
    feature_importance: list[FeatureImportanceOut]


class TutorSummaryOut(BaseModel):
    tutor_name: str
    in_observation: int
    critical_pending: int


class StudentListItemOut(BaseModel):
    id: int
    code: str
    full_name: str
    career: str
    cycle: int
    risk_level: RiskLevel
    probability: float
    main_factor: str
    reasons: list[str]
    pending_alerts: int
    last_contact_at: datetime | None


class TopFactorOut(BaseModel):
    feature: str
    group: str
    impact: float
    text: str


class RiskDetailOut(BaseModel):
    level: RiskLevel
    probability: float
    score: int
    main_factor: str
    computed_at: datetime
    top_factors: list[TopFactorOut]
    disclaimer: str


class IndicatorsOut(BaseModel):
    gpa_avg: float
    attendance_rate: float
    lms_participation: float
    tuition_debt_months: int
    weekly_work_hours: int
    family_support: int
    socioemotional_adaptation: int


class InterventionOut(BaseModel):
    id: int
    type: InterventionType
    note: str
    scheduled_at: datetime | None
    created_at: datetime
    tutor_name: str


class StudentDetailOut(BaseModel):
    id: int
    code: str
    full_name: str
    career: str
    faculty: str
    cycle: int
    risk: RiskDetailOut
    indicators: IndicatorsOut
    interventions: list[InterventionOut]


class InterventionCreate(BaseModel):
    type: InterventionType
    note: str = Field(min_length=1, max_length=500)
    scheduled_at: datetime | None = None
