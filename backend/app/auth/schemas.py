"""Pydantic models for auth router request/response payloads."""

from pydantic import BaseModel, ConfigDict, Field


class TokenSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    access_token: str = Field(min_length=1, max_length=4096)
    refresh_token: str = Field(min_length=1, max_length=4096)
    expires_at: int = Field(gt=0)
    scopes: list[str] = Field(min_length=1, max_length=20)


class TokenRefreshResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_at: int
