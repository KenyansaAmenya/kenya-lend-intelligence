import argparse
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from sklearn.model_selection import train_test_split

from app.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.services.ml.model_trainer import ModelTrainer
from app.services.ml.model_registry import ModelRegistry
from app.services.ml.data_validator import validate_training_data

logger = get_logger(__name__)


def load_training_data(data_path: str) -> pd.DataFrame:
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    validation = validate_training_data(df)
    if not validation["valid"]:
        logger.warning("data_validation_issues", issues=validation["issues"])
        
        critical = [i for i in validation["issues"] if i.get("severity") == "critical"]
        if critical:
            raise ValueError(f"Critical data issues found: {critical}")
    
    logger.info("training_data_loaded", rows=len(df), columns=len(df.columns))
    return df


def optimize_hyperparameters(model_type: str, X_train, y_train, X_val, y_val, n_trials: int = 50) -> tuple:
    import optuna
    
    def objective(trial):
        params = {}
        
        if model_type == "xgboost":
            import xgboost as xgb
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            }
            model = xgb.XGBClassifier(**params)
        elif model_type == "lightgbm":
            import lightgbm as lgb
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
                "num_leaves": trial.suggest_int("num_leaves", 31, 255),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_samples": trial.suggest_int("min_child_samples", 5, 20),
            }
            model = lgb.LGBMClassifier(**params)
        else:
            from sklearn.ensemble import RandomForestClassifier
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                "max_depth": trial.suggest_int("max_depth", 5, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            }
            model = RandomForestClassifier(**params)
        
        model.fit(X_train, y_train)
        score = model.score(X_val, y_val)
        return score
    
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    
    return study.best_params, study.best_value


def main():
    
    configure_logging()
    
    parser = argparse.ArgumentParser(description="Train Kenya Lend Intelligence ML models")
    parser.add_argument("--data-path", required=True, help="Path to training data CSV")
    parser.add_argument("--model-path", default=settings.model_path, help="Model output path")
    parser.add_argument("--models", nargs="+", choices=["credit", "default", "churn", "all"], default=["all"])
    parser.add_argument("--mlflow-tracking", default=settings.mlflow_tracking_uri, help="MLflow tracking URI")
    parser.add_argument("--experiment-name", default=f"{settings.app_name}_experiments", help="MLflow experiment name")
    parser.add_argument("--hyperopt", action="store_true", help="Enable hyperparameter optimization")
    parser.add_argument("--n-trials", type=int, default=50, help="Number of hyperopt trials")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test size for validation")
    
    args = parser.parse_args()
    
    try:
        # Load and validate data
        df = load_training_data(args.data_path)
        
        # Initialize trainer with MLflow
        trainer = ModelTrainer(
            model_path=args.model_path,
            mlflow_tracking_uri=args.mlflow_tracking_uri,
            experiment_name=args.experiment_name
        )
        
        # Split data
        train_df, test_df = train_test_split(df, test_size=args.test_size, random_state=42)
        
        # Train models
        results = {}
        
        if "all" in args.models:
            results = trainer.train_all_models(
                train_df,
                test_df=test_df,
                hyperopt=args.hyperopt,
                n_trials=args.n_trials
            )
        else:
            for model_type in args.models:
                if model_type == "credit":
                    results["credit"] = trainer.train_credit_model(train_df, test_df)
                elif model_type == "default":
                    results["default"] = trainer.train_default_model(train_df, test_df)
                elif model_type == "churn":
                    results["churn"] = trainer.train_churn_model(train_df, test_df)
        
        # Print results
        print(json.dumps(results, indent=2, default=str))
        
        # Check for failures
        failures = [k for k, v in results.items() if v.get("status") == "failed"]
        if failures:
            logger.error("training_failures", models=failures)
            sys.exit(1)
        
        logger.info("training_complete", results=results)
        sys.exit(0)
        
    except Exception as e:
        logger.error("training_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()