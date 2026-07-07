# Model Registry Service.
# This will Manage model versioning, artifacts, and metadata.

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ModelRegistry:
    def __init__(self, registry_path: str = None):
        self.registry_path = Path(registry_path or settings.model_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.registry_path / "registry.json"
        self._registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"models": {}, "active_versions": {}}
    
    def _save_registry(self) -> None:
        with open(self.registry_file, "w") as f:
            json.dump(self._registry, f, indent=2, default=str)
    
    def register_model(
        self,
        model_name: str,
        version: str,
        model_path: str,
        metrics: Dict,
        features: List[str],
        parameters: Optional[Dict] = None,
    ) -> Dict:
        if model_name not in self._registry["models"]:
            self._registry["models"][model_name] = {}
        
        entry = {
            "version": version,
            "model_path": model_path,
            "metrics": metrics,
            "features": features,
            "parameters": parameters or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "registered",
        }
        
        self._registry["models"][model_name][version] = entry
        self._save_registry()
        
        logger.info("model_registered", model=model_name, version=version)
        
        return entry
    
    def promote_model(self, model_name: str, version: str, environment: str = "production") -> Dict:
        if model_name not in self._registry["models"]:
            raise ValueError(f"Model {model_name} not found")
        
        if version not in self._registry["models"][model_name]:
            raise ValueError(f"Version {version} not found for {model_name}")
        
        # Update active version
        if "active_versions" not in self._registry:
            self._registry["active_versions"] = {}
        
        self._registry["active_versions"][f"{model_name}_{environment}"] = version
        
        # Update status
        self._registry["models"][model_name][version]["status"] = "active"
        self._registry["models"][model_name][version]["promoted_at"] = datetime.now(timezone.utc).isoformat()
        self._registry["models"][model_name][version]["environment"] = environment
        
        self._save_registry()
        
        logger.info("model_promoted", model=model_name, version=version, environment=environment)
        
        return self._registry["models"][model_name][version]
    
    def get_active_model(self, model_name: str, environment: str = "production") -> Optional[Dict]:
        """Get currently active model for environment."""
        key = f"{model_name}_{environment}"
        version = self._registry.get("active_versions", {}).get(key)
        
        if version and model_name in self._registry["models"]:
            return self._registry["models"][model_name].get(version)
        return None
    
    def list_models(self, model_name: Optional[str] = None) -> Dict:
        if model_name:
            return self._registry["models"].get(model_name, {})
        return self._registry["models"]
    
    def get_model_history(self, model_name: str) -> List[Dict]:
        versions = self._registry["models"].get(model_name, {})
        return sorted(
            versions.values(),
            key=lambda x: x.get("registered_at", ""),
            reverse=True,
        )
    
    def rollback_model(self, model_name: str, environment: str = "production") -> Optional[Dict]:
        history = self.get_model_history(model_name)
        if len(history) < 2:
            logger.warning("rollback_not_possible", model=model_name, reason="insufficient_versions")
            return None
        
        # Find current and previous active versions
        current = self.get_active_model(model_name, environment)
        if not current:
            return None
        
        # Find previous version
        current_idx = None
        for i, h in enumerate(history):
            if h["version"] == current["version"]:
                current_idx = i
                break
        
        if current_idx is not None and current_idx + 1 < len(history):
            previous = history[current_idx + 1]
            return self.promote_model(model_name, previous["version"], environment)
        
        return None
    
    # TODO: Integrate with MLflow Model Registry
    # TODO: Add model artifact cloud storage
    # TODO: Add model approval workflow
    # TODO: Add A/B test model management