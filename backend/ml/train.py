import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import Engine
from sqlmodel import Session, select
from xgboost import XGBClassifier

from app.db import create_db_and_tables, engine
from app.models import HistoricalCohort, ModelVersion
from app.services.scoring import score_students
from ml.explain import build_explainer
from ml.features import FEATURE_COLUMNS, feature_frame
from ml.generate_data import SEED

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
CLASSIFICATION_THRESHOLD = 0.5
N_ESTIMATORS = 300
MAX_DEPTH = 4
LEARNING_RATE = 0.05
SUBSAMPLE = 0.9
COLSAMPLE_BY_TREE = 0.9
MIN_CHILD_WEIGHT = 2.0


def train_model(engine: Engine, artifacts_dir: Path = ARTIFACTS_DIR) -> dict[str, Any]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        historical = session.exec(select(HistoricalCohort)).all()
        if not historical:
            raise RuntimeError("No historical data found. Run `make seed` first.")

        frame = feature_frame(historical)
        labels = np.array([row.dropped_out for row in historical], dtype=int)

        x_train, x_test, y_train, y_test = train_test_split(
            frame,
            labels,
            test_size=0.2,
            random_state=SEED,
            stratify=labels,
        )

        positive_weight = (y_train == 0).sum() / max(1, (y_train == 1).sum())
        model = XGBClassifier(
            n_estimators=N_ESTIMATORS,
            max_depth=MAX_DEPTH,
            learning_rate=LEARNING_RATE,
            subsample=SUBSAMPLE,
            colsample_bytree=COLSAMPLE_BY_TREE,
            min_child_weight=MIN_CHILD_WEIGHT,
            scale_pos_weight=float(positive_weight),
            random_state=SEED,
            eval_metric="logloss",
            tree_method="hist",
            n_jobs=4,
        )
        model.fit(x_train, y_train)

        test_probabilities = model.predict_proba(x_test)[:, 1]
        test_predictions = (test_probabilities >= CLASSIFICATION_THRESHOLD).astype(int)
        metrics = {
            "f1": float(f1_score(y_test, test_predictions)),
            "precision": float(precision_score(y_test, test_predictions)),
            "recall": float(recall_score(y_test, test_predictions)),
            "pr_auc": float(average_precision_score(y_test, test_probabilities)),
        }

        model_path = artifacts_dir / "xgb_model.json"
        model.save_model(model_path)
        (artifacts_dir / "feature_columns.json").write_text(
            json.dumps(FEATURE_COLUMNS, indent=2) + "\n",
            encoding="utf-8",
        )

        feature_importance = [
            {"feature": feature, "importance": round(float(importance), 6)}
            for feature, importance in sorted(
                zip(FEATURE_COLUMNS, model.feature_importances_),
                key=lambda item: item[1],
                reverse=True,
            )
        ]

        for previous in session.exec(select(ModelVersion)).all():
            previous.is_active = False

        model_version = ModelVersion(
            algorithm="XGBoost",
            n_train=len(x_train),
            f1=metrics["f1"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            pr_auc=metrics["pr_auc"],
            threshold={},
            feature_importance=feature_importance,
            is_active=True,
            data_source="synthetic",
        )
        session.add(model_version)
        session.flush()

        explainer = build_explainer(model)
        scoring_summary = score_students(session, model, explainer, model_version)

        session.commit()

    summary = {
        **metrics,
        **scoring_summary,
        "model_path": str(model_path),
        "n_train": len(x_train),
        "n_test": len(x_test),
    }
    (artifacts_dir / "metrics.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    create_db_and_tables()
    summary = train_model(engine)

    print("Modelo entrenado y estudiantes puntuados")
    print(f"  F1: {summary['f1']:.3f}")
    print(f"  Precisión: {summary['precision']:.3f}")
    print(f"  Recall: {summary['recall']:.3f}")
    print(f"  PR-AUC: {summary['pr_auc']:.3f}")
    print(
        f"  Distribución: alto {summary['high']} ({summary['high_pct']}%), "
        f"medio {summary['medium']} ({summary['medium_pct']}%), "
        f"bajo {summary['low']} ({summary['low_pct']}%)"
    )
    print(
        f"  Umbrales: alto {summary['high_threshold']:.4f} · "
        f"medio {summary['medium_threshold']:.4f}"
    )
    print(f"  Artefacto: {summary['model_path']}")

    if summary["f1"] < 0.55:
        print("ADVERTENCIA: F1 por debajo de 0.55; no se ajustó el generador.")


if __name__ == "__main__":
    main()
