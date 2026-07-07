# Credit Scoring Model.
# Implements the credit scoring model using ensemble methods.

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

from app.config import settings
from app.services.ml.base_model import BaseMLModel

class CreditScoringModel(BaseMLModel):
    def __init__(self, version: str = "1.0.0"):
        super().__init__("credit_scoring", version)
        self.scaler = StandardScaler()
    
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, float]:
        self.feature_columns = list(X.columns)
        
        # Preprocess
        X_scaled = self.scaler.fit_transform(X)
        self.preprocessor = self.scaler
        
        # Train ensemble model
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=settings.random_state,
        )
        
        self.model.fit(X_scaled, y)
        
        # Cross-validation
        scores = cross_val_score(
            self.model, X_scaled, y, cv=5, scoring="neg_mean_squared_error"
        )
        
        self.metrics = {
            "cv_rmse": float(np.sqrt(-scores.mean())),
            "cv_std": float(scores.std()),
            "feature_count": len(self.feature_columns),
        }
        
        self.is_trained = True
        return self.metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        X_scaled = self.preprocessor.transform(X)
        raw_scores = self.model.predict(X_scaled)
        
        # Scale to 300-850 range
        scores = np.clip(raw_scores, 300, 850)
        return scores
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        scores = self.predict(X)
        # Normalize to 0-1 for probability interpretation
        return (scores - 300) / 550
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        predictions = self.predict(X)
        
        return {
            "rmse": float(np.sqrt(mean_squared_error(y, predictions))),
            "mae": float(mean_absolute_error(y, predictions)),
            "r2": float(r2_score(y, predictions)),
        }
    
    def get_score_factors(self, X: pd.DataFrame, idx: int = 0) -> List[Dict]:
        importance = self.get_feature_importance()
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {
                "factor": name,
                "impact": "positive" if importance > 0.05 else "neutral",
                "weight": float(importance),
            }
            for name, importance in top_features
        ]
    
    # TODO: Add fairness-aware training
    # TODO: Add score explainability with SHAP
    # TODO: Add model calibration for probability outputs