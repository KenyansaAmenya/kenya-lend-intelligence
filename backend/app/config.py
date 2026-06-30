from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE",".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application Settings
    app_name: str = Field(default="KenyaLendIntelligence", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode flag")
    environment: str = Field(default="development", description="Environment name")
    secret_key: str = Field(..., description="Secret key for JWT signing")
    access_token_expire_minutes: int = Field(default=30, description="JWT access token expiry")
    refresh_token_expire_days: int = Field(default=7, description="JWT refresh token expiry")
    
    # Database Settings
    database_url: str = Field(..., description="Async database URL")
    database_url_sync: str = Field(..., description="Sync database URL for migrations")
    
    # Supabase Settings
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    supabase_service_key: str = Field(..., description="Supabase service role key")
    
    storage_bucket_raw: str = Field(default="raw-statements", description="Raw data bucket")
    storage_bucket_processed: str = Field(default="processed-data", description="Processed data bucket")
    storage_bucket_models: str = Field(default="ml-models", description="ML models bucket")
    storage_bucket_artifacts: str = Field(default="ml-artifacts", description="ML artifacts bucket")
    
    # Security Settings
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    bcrypt_rounds: int = Field(default=12, description="Bcrypt hashing rounds")
    cors_origins: str = Field(default="http://localhost:3000", description="CORS allowed origins")
    rate_limit_per_minute: int = Field(default=60, description="API rate limit per minute")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        if instance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v    
    
    # ML Model Settings
    model_path: str = Field(default="./ml/models", description="Path to ML models")
    credit_model_path: str = Field(default="./ml/models/credit_model.pkl", description="Credit model path")
    default_model_path: str = Field(default="./ml/models/default_model.pkl", description="Default model path")
    churn_model_path: str = Field(default="./ml/models/churn_model.pkl", description="Churn model path")
    preprocessor_path: str = Field(default="./ml/models/preprocessor.pkl", description="Preprocessor path")
    model_versioning: str = Field(default="latest", description="Model version to use")
    model_registry_url: Optional[str] = Field(default=None, description="MLflow registry URL")
    model_auto_load: bool = Field(default=True, description="Auto-load models on startup")
    
    train_test_split: float = Field(default=0.7, description="Training data split ratio")
    validation_split: float = Field(default=0.15, description="Validation data split ratio")
    test_split: float = Field(default=0.15, description="Test data split ratio")
    random_state: int = Field(default=42, description="Random seed for reproducibility")
    n_trials_optuna: int = Field(default=100, description="Number of Optuna optimization trials")
 
    # Churn Configuration
    churn_inactivity_days: int = Field(default=90, description="Days of inactivity to define churn")
    churn_lookback_days: int = Field(default=30, description="Lookback period for churn features")
 
    # Credit Scoring
    min_credit_score: int = Field(default=300, description="Minimum credit score")
    max_credit_score: int = Field(default=850, description="Maximum credit score")
    base_interest_rate: float = Field(default=0.15, description="Base interest rate")
    max_interest_rate: float = Field(default=0.36, description="Maximum interest rate")
    
    # External Data Connectors
    world_bank_api_url: str = Field(default="https://api.worldbank.org/v2", description="World Bank API URL")
    kaggle_username: Optional[str] = Field(default=None, description="Kaggle username")
    kaggle_key: Optional[str] = Field(default=None, description="Kaggle API key")

    # M-PESA Integration 
    mpesa_consumer_key: Optional[str] = Field(default=None)
    mpesa_consumer_secret: Optional[str] = Field(default=None)
    mpesa_passkey: Optional[str] = Field(default=None)
    mpesa_shortcode: str = Field(default="174379")
    mpesa_callback_url: Optional[str] = Field(default=None)
    mpesa_timeout_url: Optional[str] = Field(default=None)
    mpesa_environment: str = Field(default="sandbox") 
   
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/console)")
  
    # Feature Engineering
    max_features: int = Field(default=40, description="Maximum number of features")
    feature_store_enabled: bool = Field(default=False, description="Feature store enabled flag")
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in str(self.cors_origins).split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Global settings instance for easy import
settings = get_settings()



# Future Enhancements:
    # - Add Vault integration for secrets management
    # - Add feature flags for A/B testing
    # - Add multi-tenant configuration support

# TODO: Add Vault integration for dynamic secret rotation
# TODO: Add feature flag integration for A/B testing
# TODO: Add configuration validation against a schema registry