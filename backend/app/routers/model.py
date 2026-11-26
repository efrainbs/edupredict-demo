from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import require_role
from app.models import ModelVersion, User
from app.schemas import (
    FeatureImportanceOut,
    ModelInfoOut,
    ModelMetricsOut,
)

router = APIRouter(tags=["model"])

DirectorDep = Annotated[User, Depends(require_role("director"))]

DISCLAIMER = (
    "Métricas sobre datos sintéticos — no son evidencia de desempeño real"
)


@router.get("/model/info", response_model=ModelInfoOut)
def model_info(
    _user: DirectorDep,
    session: Annotated[Session, Depends(get_session)],
) -> ModelInfoOut:
    from ml.features import FEATURE_LABELS

    model = session.exec(
        select(ModelVersion).where(ModelVersion.is_active == True)  # noqa: E712
    ).first()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay un modelo entrenado",
        )

    importance = [
        FeatureImportanceOut(
            feature=item["feature"],
            label=FEATURE_LABELS.get(item["feature"], item["feature"]),
            importance=item["importance"],
        )
        for item in model.feature_importance[:10]
    ]

    return ModelInfoOut(
        algorithm=model.algorithm,
        trained_at=model.trained_at,
        n_train=model.n_train,
        metrics=ModelMetricsOut(
            f1=model.f1,
            precision=model.precision,
            recall=model.recall,
            pr_auc=model.pr_auc,
        ),
        data_source=model.data_source,
        disclaimer=DISCLAIMER,
        feature_importance=importance,
    )
