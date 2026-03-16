"""Pydantic v2 schemas for user endpoints."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, extra="forbid", str_strip_whitespace=True
    )

    id: str = Field(..., max_length=255)
    email: EmailStr = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    picture: str | None = Field(None, max_length=2048)
    granted_scopes: list[str] = Field(default_factory=list)


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    timezone: str = Field(default="UTC", max_length=100)
    default_calendar: str = Field(default="primary", max_length=100)


class UpdatePreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    timezone: str | None = Field(default=None, max_length=100)
    default_calendar: str | None = Field(default=None, max_length=100)
