from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-secret-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SmartMaintain AI"
    debug: bool = True
    port: int = 8080
    aws_region: str = "us-east-1"

    # Storage mode: memory for local dev, dynamodb for AWS
    storage_backend: Literal["memory", "dynamodb"] = "memory"

    # Seed demo data only when explicitly enabled (default: only in debug mode)
    seed_demo_data: bool | None = None

    # DynamoDB table names
    machines_table: str = "smartmaintain-machines"
    alerts_table: str = "smartmaintain-alerts"
    work_orders_table: str = "smartmaintain-work-orders"
    inspections_table: str = "smartmaintain-inspections"
    users_table: str = "smartmaintain-users"

    # S3 buckets
    sensor_bucket: str = "smartmaintain-sensor-data"
    document_bucket: str = "smartmaintain-documents"

    # AI services
    use_local_model: bool = True
    sagemaker_endpoint: str = ""
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    model_version: str = "1.0.0-local"
    ai_timeout_seconds: int = 10
    ai_max_retries: int = 2
    max_upload_size_mb: int = 10

    # Auth
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    auth_mode: Literal["local", "cognito"] = "local"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_region: str = "us-east-1"

    # Rate limiting
    login_rate_limit_attempts: int = 10
    login_rate_limit_window_seconds: int = 300

    # Alert thresholds
    anomaly_threshold: float = 0.65
    failure_threshold: float = 0.70
    critical_failure_threshold: float = 0.85

    # CORS — explicit origins only; never use wildcard with credentials
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]

    # SNS
    sns_topic_arn: str = ""

    # Static files
    static_dir: str = "app/static"

    # Use lightweight rule-based predictions (no scikit-learn) for constrained hosts
    lightweight_predictions: bool = False

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret_strength(cls, v: str, info) -> str:
        debug = info.data.get("debug", True)
        if not debug:
            if v == DEFAULT_JWT_SECRET or len(v) < 32:
                raise ValueError(
                    "JWT_SECRET must be set to a strong random value (min 32 chars) when DEBUG=false"
                )
        return v

    @model_validator(mode="after")
    def apply_defaults(self) -> "Settings":
        if self.seed_demo_data is None:
            self.seed_demo_data = self.debug
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
