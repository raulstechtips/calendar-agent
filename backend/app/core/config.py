"""Application settings loaded from environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Azure OpenAI — no API key; uses DefaultAzureCredential
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_embed_deployment: str = "text-embedding-3-small"

    # Azure Managed Identity (optional — only needed in prod for User Assigned Identity)
    azure_managed_identity_client_id: str = ""

    # Azure AI Search — no API key; uses DefaultAzureCredential
    azure_search_endpoint: str = ""
    azure_search_index: str = "calendar-context"

    # Azure AI Content Safety — no API key; uses DefaultAzureCredential
    azure_content_safety_endpoint: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    fernet_key: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]
    canary_token: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string or list, rejecting wildcard origins."""
        if isinstance(v, str):
            origins = [o.strip() for o in v.split(",") if o.strip()]
        else:
            origins = [o.strip() for o in v if o.strip()]
        if "*" in origins:
            raise ValueError(
                "CORS wildcard '*' is not allowed when credentials are enabled"
            )
        return origins


settings = Settings()
