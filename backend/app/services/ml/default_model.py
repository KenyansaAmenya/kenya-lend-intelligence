# Default Prediction Model.
# It Implements the probability of default (PD) model using
# gradient boosting classifiers.

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.services.ml.base_model import BaseMLModel

class DefaultPredictionModel(BaseMLModel):
    def __init__(self, version: str = "1.0.0"):
        super().__init__("default_prediction", version)
        self.scaler = StandardScaler()
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, float]:
        self.feature_columns = list(X.columns)
        
        # Handle class imbalance with SMOTE
        from imblearn.over_sampling import SMOTE
        
        smote = SMOTE(random_state=settings.random_state)
        X_resampled, y_resampled = smote.fit_resample(X, y)
        
        # Preprocess
        X_scaled = self.scaler.fit_transform(X_resampled)
        self.preprocessor = self.scaler
        
        # Train model
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=settings.random_state,
        )
        
        self.model.fit(X_scaled, y_resampled)
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_scaled, y_resampled, cv=5, scoring="roc_auc"
        )
        
        self.metrics = {
            "cv_auc_roc": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_count": len(self.feature_columns),
            "training_samples": len(X_resampled),
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        X_scaled = self.preprocessor.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        X_scaled = self.preprocessor.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        predictions = self.predict(X)
        probabilities = self.predict_proba(X)[:, 1]
        
        return {
            "accuracy": float(accuracy_score(y, predictions)),
            "precision": float(precision_score(y, predictions, zero_division=0)),
            "recall": float(recall_score(y, predictions, zero_division=0)),
            "auc_roc": float(roc_auc_score(y, probabilities)),
        }
    
    # TODO: Add survival analysis for time-to-default
    # TODO: Add macroeconomic stress testing
    # TODO: Add model calibration for probability outputs