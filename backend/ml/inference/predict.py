# Model Inference Script

import argparse
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from prometheus_client import Counter, Histogram

from app.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.services.ml.churn_model import ChurnPredictionModel
from app.services.ml.credit_model import CreditScoringModel
from app.services.ml.default_model import DefaultPredictionModel

logger = get_logger(__name__)

# Prometheus metrics
prediction_counter = Counter(
    'predictions_total',
    'Total predictions made',
    ['model_name', 'status']
)

prediction_latency = Histogram(
    'prediction_latency_seconds',
    'Prediction latency',
    ['model_name']
)


def load_model(model_name: str, model_path: str):
    path = Path(model_path) / f"{model_name}_model.pkl"
    
    # Check for version-specific model
    if hasattr(settings, "model_version"):
        version_path = Path(model_path) / f"{model_name}_model_{settings.model_version}.pkl"
        if version_path.exists():
            path = version_path
    
    if model_name == "credit":
        model = CreditScoringModel()
    elif model_name == "default":
        model = DefaultPredictionModel()
    elif model_name == "churn":
        model = ChurnPredictionModel()
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    model.load(str(path))
    logger.info("model_loaded", model_name=model_name, path=str(path))
    return model

def validate_features(df: pd.DataFrame, model_name: str, feature_columns: List[str]) -> pd.DataFrame:
    # Check for missing columns
    missing_cols = set(feature_columns) - set(df.columns)
    if missing_cols:
        logger.warning("missing_features", columns=list(missing_cols))
        for col in missing_cols:
            df[col] = 0
    
    # Select only required features
    X = df[feature_columns].copy()
    
    # Fill missing values
    X = X.fillna(0)
    
    return X

def run_inference(
    model_name: str,
    input_path: str,
    output_path: str,
    model_path: str,
    batch_size: int = 1000
) -> None:
    start_time = time.perf_counter()
    
    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info("inference_data_loaded", rows=len(df))
        
        # Load model
        model = load_model(model_name, model_path)
        feature_columns = getattr(model, "feature_columns", [])
        
        # Process in chunks
        all_results = []
        total_chunks = (len(df) + batch_size - 1) // batch_size
        
        for chunk_idx in range(total_chunks):
            start_idx = chunk_idx * batch_size
            end_idx = min((chunk_idx + 1) * batch_size, len(df))
            
            chunk = df.iloc[start_idx:end_idx]
            X = validate_features(chunk, model_name, feature_columns)
            
            # Predict
            predictions = model.predict(X)
            
            # Collect results
            for i in range(len(chunk)):
                result = {
                    "customer_id": str(chunk.iloc[i].get("customer_id", start_idx + i)),
                    "prediction": float(predictions[i]),
                }
                
                if hasattr(model, "predict_proba"):
                    probabilities = model.predict_proba(X)[:, 1]
                    result["probability"] = float(probabilities[i])
                
                all_results.append(result)
            
            logger.info("chunk_processed", chunk=chunk_idx + 1, total=total_chunks)
        
        # Save results
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "w") as f:
            json.dump(all_results, f, indent=2)
        
        # Update metrics
        latency = time.perf_counter() - start_time
        prediction_counter.labels(model_name=model_name, status="success").inc(len(all_results))
        prediction_latency.labels(model_name=model_name).observe(latency)
        
        logger.info("inference_complete", results=len(all_results), output=str(output), latency=latency)
        
    except Exception as e:
        prediction_counter.labels(model_name=model_name, status="failure").inc()
        logger.error("inference_failed", error=str(e))
        raise

def main():
    configure_logging()
    
    parser = argparse.ArgumentParser(description="Run Kenya Lend Intelligence model inference")
    parser.add_argument("--model", required=True, choices=["credit", "default", "churn"])
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--model-path", default=settings.model_path)
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    
    args = parser.parse_args()
    
    run_inference(args.model, args.input, args.output, args.model_path, args.batch_size)


if __name__ == "__main__":
    main()