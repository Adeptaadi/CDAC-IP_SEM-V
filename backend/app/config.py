import os

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field

    class Settings(BaseSettings):
        ENVIRONMENT: str = Field(default="development")
        LOG_LEVEL: str = Field(default="INFO")
        SECRET_KEY: str = Field(default="sentinel_dev_secret_key_change_in_production_32bytes!")
        ALGORITHM: str = Field(default="HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

        # Database
        DATABASE_URL: str = Field(default="postgresql://sentinel_dev:sentinel_secure_pass@db:5432/sentinel")
        
        # Redis
        REDIS_URL: str = Field(default="redis://cache:6379/0")

        # ChromaDB
        CHROMA_PERSIST_DIR: str = Field(default="/app/chroma_data")
        CHROMA_HOST: str = Field(default="vector-db")
        CHROMA_PORT: int = Field(default=8000)

        # LLM & AI
        OLLAMA_HOST: str = Field(default="http://host.docker.internal:11434")
        PRIMARY_LLM_MODEL: str = Field(default="qwen2.5:latest")
        EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")

        # Planner thresholds (from Implementation_Specification.md §1 & §3)
        MAX_PLANNING_CYCLES: int = Field(default=15)
        CONFIDENCE_AUTO_COMPLETE_THRESHOLD: float = Field(default=0.85)
        STAGNATION_CYCLE_LIMIT: int = Field(default=3)

        # Confidence factor weights (sum to 1.0 from IS §1.3)
        WEIGHT_DETECTION: float = Field(default=0.15)
        WEIGHT_EVIDENCE: float = Field(default=0.20)
        WEIGHT_CORRELATION: float = Field(default=0.15)
        WEIGHT_KNOWLEDGE: float = Field(default=0.15)
        WEIGHT_AGREEMENT: float = Field(default=0.15)
        WEIGHT_HISTORICAL: float = Field(default=0.20)

        class Config:
            env_file = ".env"
            extra = "allow"

    settings = Settings()

except ImportError:
    # Fallback for lightweight local environments without pydantic-settings
    class FallbackSettings:
        ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        SECRET_KEY = os.getenv("SECRET_KEY", "sentinel_dev_secret_key_change_in_production_32bytes!")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinel_dev:sentinel_secure_pass@db:5432/sentinel")
        REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")
        CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/app/chroma_data")
        CHROMA_HOST = os.getenv("CHROMA_HOST", "vector-db")
        CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
        OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        PRIMARY_LLM_MODEL = os.getenv("PRIMARY_LLM_MODEL", "qwen2.5:latest")
        EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        MAX_PLANNING_CYCLES = int(os.getenv("MAX_PLANNING_CYCLES", "15"))
        CONFIDENCE_AUTO_COMPLETE_THRESHOLD = float(os.getenv("CONFIDENCE_AUTO_COMPLETE_THRESHOLD", "0.85"))
        STAGNATION_CYCLE_LIMIT = int(os.getenv("STAGNATION_CYCLE_LIMIT", "3"))
        WEIGHT_DETECTION = float(os.getenv("WEIGHT_DETECTION", "0.15"))
        WEIGHT_EVIDENCE = float(os.getenv("WEIGHT_EVIDENCE", "0.20"))
        WEIGHT_CORRELATION = float(os.getenv("WEIGHT_CORRELATION", "0.15"))
        WEIGHT_KNOWLEDGE = float(os.getenv("WEIGHT_KNOWLEDGE", "0.15"))
        WEIGHT_AGREEMENT = float(os.getenv("WEIGHT_AGREEMENT", "0.15"))
        WEIGHT_HISTORICAL = float(os.getenv("WEIGHT_HISTORICAL", "0.20"))

    settings = FallbackSettings()
