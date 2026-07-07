# Model Explainability Service.
# Provides SHAP-based explanations for model predictions.

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ExplainabilityService:
    def __init__(self):
        self.explanations_cache = {}
    
    def explain_prediction(
        self,
        model,
        X: pd.DataFrame,
        instance_idx: int = 0,
        feature_names: Optional[List[str]] = None,
    ) -> Dict:
        try:
            import shap
            
            # Create explainer
            explainer = shap.TreeExplainer(model)
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(X.iloc[instance_idx:instance_idx+1])
            
            # Handle binary classification
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class
            
            # Build explanation
            features = feature_names or list(X.columns)
            instance_values = X.iloc[instance_idx].values
            
            shap_dict = {}
            for i, (feature, value, shap_val) in enumerate(zip(features, instance_values, shap_values[0])):
                shap_dict[feature] = {
                    "value": float(value),
                    "shap_value": float(shap_val),
                    "impact": "positive" if shap_val > 0 else "negative",
                    "magnitude": abs(float(shap_val)),
                }
            
            # Sort by magnitude
            sorted_features = sorted(
                shap_dict.items(),
                key=lambda x: x[1]["magnitude"],
                reverse=True,
            )
            
            return {
                "base_value": float(explainer.expected_value[1] if isinstance(explainer.expected_value, list) else explainer.expected_value),
                "prediction": float(model.predict_proba(X.iloc[instance_idx:instance_idx+1])[0][1]),
                "features": dict(sorted_features[:10]),  # Top 10 features
                "top_positive": [
                    {"feature": k, "contribution": v["shap_value"]}
                    for k, v in sorted_features[:5] if v["shap_value"] > 0
                ],
                "top_negative": [
                    {"feature": k, "contribution": v["shap_value"]}
                    for k, v in sorted_features[:5] if v["shap_value"] < 0
                ],
            }
            
        except ImportError:
            logger.warning("shap_not_available")
            return self._fallback_explanation(model, X, instance_idx, feature_names)
        except Exception as e:
            logger.error("shap_explanation_error", error=str(e))
            return self._fallback_explanation(model, X, instance_idx, feature_names)
    
    def _fallback_explanation(
        self,
        model,
        X: pd.DataFrame,
        instance_idx: int,
        feature_names: Optional[List[str]] = None,
    ) -> Dict:
        """Fallback explanation using feature importance."""
        features = feature_names or list(X.columns)
        
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            feature_imp = list(zip(features, importances))
            feature_imp.sort(key=lambda x: x[1], reverse=True)
            
            return {
                "base_value": 0.5,
                "prediction": float(model.predict_proba(X.iloc[instance_idx:instance_idx+1])[0][1]) if hasattr(model, "predict_proba") else 0.5,
                "features": {
                    f: {"value": float(X.iloc[instance_idx][f]), "importance": float(imp)}
                    for f, imp in feature_imp[:10]
                },
                "top_positive": [{"feature": f, "contribution": imp} for f, imp in feature_imp[:5]],
                "top_negative": [],
                "note": "Fallback explanation - SHAP not available",
            }
        
        return {
            "base_value": 0.5,
            "prediction": 0.5,
            "features": {},
            "note": "Explanation not available",
        }
    
    def get_global_feature_importance(self, model, feature_names: Optional[List[str]] = None) -> List[Dict]:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            names = feature_names or [f"feature_{i}" for i in range(len(importances))]
            
            return [
                {"feature": name, "importance": float(imp)}
                for name, imp in sorted(zip(names, importances), key=lambda x: x[1], reverse=True)
            ]
        
        return []
    
    # TODO: Add LIME explanations
    # TODO: Add counterfactual explanations
    # TODO: Add fairness metrics calculation
    # TODO: Add explanation caching