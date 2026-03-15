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
