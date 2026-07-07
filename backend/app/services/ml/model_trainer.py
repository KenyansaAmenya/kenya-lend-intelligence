# My Model Training Pipeline.

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from app.config import settings
from app.core.logging_config import get_logger
from app.services.ml.churn_model import ChurnPredictionModel
from app.services.ml.credit_model import CreditScoringModel
from app.services.ml.default_model import DefaultPredictionModel

logger = get_logger(__name__)

class ModelTrainer:
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path or settings.model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.credit_model = CreditScoringModel()
        self.default_model = DefaultPredictionModel()
        self.churn_model = ChurnPredictionModel()
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        if feature_columns is None:
            feature_columns = [c for c in df.columns if c != target_column and c != "customer_id"]
        
        X = df[feature_columns].fillna(0)
        y = df[target_column]
        
        # First split: train+val vs test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=settings.test_split,
            random_state=settings.random_state,
            stratify=y if y.nunique() <= 10 else None,
        )
        
        # Second split: train vs val
        val_size = settings.validation_split / (settings.train_test_split + settings.validation_split)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size,
            random_state=settings.random_state,
            stratify=y_temp if y_temp.nunique() <= 10 else None,
        )
        
        logger.info(
            "data_prepared",
            train_size=len(X_train),
            val_size=len(X_val),
            test_size=len(X_test),
            features=len(feature_columns),
        )
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def train_credit_model(self, df: pd.DataFrame) -> Dict[str, any]:
        logger.info("training_credit_model")
        
        X_train, y_train, X_val, y_val, X_test, y_test = self.prepare_data(
            df, target_column="credit_score"
        )
        
        # Train
        train_metrics = self.credit_model.train(X_train, y_train)
        
        # Evaluate
        val_metrics = self.credit_model.evaluate(X_val, y_val)
        test_metrics = self.credit_model.evaluate(X_test, y_test)
        
        # Save
        model_file = self.model_path / "credit_model.pkl"
        self.credit_model.save(str(model_file))
        
        # Save feature columns
        feature_file = self.model_path / "feature_columns.json"
        with open(feature_file, "w") as f:
            json.dump(self.credit_model.feature_columns, f)
        
        # Save metadata
        metadata = {
            "model_name": "credit_scoring",
            "version": self.credit_model.version,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "test_metrics": test_metrics,
            "feature_count": len(self.credit_model.feature_columns),
        }
        
        metadata_file = self.model_path / "model_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info("credit_model_trained", metrics=test_metrics)
        
        return {
            "model": "credit_scoring",
            "status": "success",
            "metrics": test_metrics,
            "model_path": str(model_file),
        }
    
    def train_default_model(self, df: pd.DataFrame) -> Dict[str, any]:
        logger.info("training_default_model")
        
        X_train, y_train, X_val, y_val, X_test, y_test = self.prepare_data(
            df, target_column="defaulted"
        )
        
        # Train
        train_metrics = self.default_model.train(X_train, y_train)
        
        # Evaluate
        val_metrics = self.default_model.evaluate(X_val, y_val)
        test_metrics = self.default_model.evaluate(X_test, y_test)
        
        # Save
        model_file = self.model_path / "default_model.pkl"
        self.default_model.save(str(model_file))
        
        logger.info("default_model_trained", metrics=test_metrics)
        
        return {
            "model": "default_prediction",
            "status": "success",
            "metrics": test_metrics,
            "model_path": str(model_file),
        }
    
    def train_churn_model(self, df: pd.DataFrame) -> Dict[str, any]:
        logger.info("training_churn_model")
        
        X_train, y_train, X_val, y_val, X_test, y_test = self.prepare_data(
            df, target_column="churned"
        )
        
        # Train
        train_metrics = self.churn_model.train(X_train, y_train)
        
        # Evaluate
        val_metrics = self.churn_model.evaluate(X_val, y_val)
        test_metrics = self.churn_model.evaluate(X_test, y_test)
        
        # Save
        model_file = self.model_path / "churn_model.pkl"
        self.churn_model.save(str(model_file))
        
        logger.info("churn_model_trained", metrics=test_metrics)
        
        return {
            "model": "churn_prediction",
            "status": "success",
            "metrics": test_metrics,
            "model_path": str(model_file),
        }
    
    def train_all_models(self, df: pd.DataFrame) -> Dict[str, any]:
        results = {}
        
        try:
            results["credit"] = self.train_credit_model(df)
        except Exception as e:
            logger.error("credit_training_failed", error=str(e))
            results["credit"] = {"status": "failed", "error": str(e)}
        
        try:
            results["default"] = self.train_default_model(df)
        except Exception as e:
            logger.error("default_training_failed", error=str(e))
            results["default"] = {"status": "failed", "error": str(e)}
        
        try:
            results["churn"] = self.train_churn_model(df)
        except Exception as e:
            logger.error("churn_training_failed", error=str(e))
            results["churn"] = {"status": "failed", "error": str(e)}
        
        return results
    
    # TODO: Add Optuna hyperparameter optimization
    # TODO: Add MLflow experiment tracking
    # TODO: Add automated retraining pipeline
    # TODO: Add model comparison and selection