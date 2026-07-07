# Base ML Model.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

class BaseMLModel(ABC):
    def __init__(self, model_name: str, version: str = "1.0.0"):
        self.model_name = model_name
        self.version = version
        self.model: Optional[Any] = None
        self.preprocessor: Optional[Any] = None
        self.feature_columns: List[str] = []
        self.metrics: Dict[str, float] = {}
        self.is_trained = False
    
    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series, **kwargs) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        pass
    
    @abstractmethod
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        pass
    
    def get_feature_importance(self) -> Dict[str, float]:
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            return dict(zip(self.feature_columns, importances))
        return {}
    
    def save(self, path: str) -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "preprocessor": self.preprocessor,
                "feature_columns": self.feature_columns,
                "metrics": self.metrics,
                "version": self.version,
                "model_name": self.model_name,
            }, f)
    
    def load(self, path: str) -> None:
        import pickle
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.preprocessor = data.get("preprocessor")
            self.feature_columns = data.get("feature_columns", [])
            self.metrics = data.get("metrics", {})
            self.version = data.get("version", "1.0.0")
            self.is_trained = True
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "is_trained": self.is_trained,
            "feature_count": len(self.feature_columns),
            "metrics": self.metrics,
        }
    
    # TODO: Add MLflow experiment tracking integration
    # TODO: Add model lineage and provenance tracking
    # TODO: Add model performance degradation detection