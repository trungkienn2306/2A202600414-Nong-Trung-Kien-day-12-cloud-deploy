"""Production config — 12-Factor: tất cả từ environment variables."""
import os
import logging
from dataclasses import dataclass, field


@dataclass
class Settings:
    # Server
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # App
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    # LLM
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))

    # Security — empty default forces explicit set in all environments
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", ""))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", ""))
    allowed_origins: list = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )

    # Rate limiting — 10 req/min per user (production requirement)
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    )

    # Budget — $10/month per user (monthly, not daily)
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))
    )

    # Storage
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    def validate(self) -> "Settings":
        logger = logging.getLogger(__name__)
        # Require keys in ALL environments (not just production)
        if not self.agent_api_key:
            dev_key = "dev-key-change-me"
            logger.warning(f"AGENT_API_KEY not set — using insecure default: {dev_key}")
            self.agent_api_key = dev_key
        if not self.jwt_secret:
            dev_secret = "dev-jwt-secret-change-me"
            logger.warning(f"JWT_SECRET not set — using insecure default")
            self.jwt_secret = dev_secret
        if self.environment == "production":
            if self.agent_api_key in ("", "dev-key-change-me"):
                raise ValueError("AGENT_API_KEY must be set to a strong secret in production!")
            if self.jwt_secret in ("", "dev-jwt-secret-change-me"):
                raise ValueError("JWT_SECRET must be set to a strong secret in production!")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set — using mock LLM")
        if not self.redis_url:
            logger.warning("REDIS_URL not set — using in-memory fallback (not scalable!)")
        return self


settings = Settings().validate()
