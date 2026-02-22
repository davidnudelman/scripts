from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Domain ────────────────────────────────────────────────
class DomainCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    active: bool = True


class DomainUpdate(BaseModel):
    active: Optional[bool] = None


class DomainResponse(BaseModel):
    id: int
    name: str
    active: bool
    created_at: datetime
    user_count: int = 0

    class Config:
        from_attributes = True


# ── User ──────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = ""
    quota: int = Field(default=1073741824, ge=0)
    active: bool = True
    is_admin: bool = False


class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    display_name: Optional[str] = None
    quota: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    quota: int
    active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Alias ─────────────────────────────────────────────────
class AliasCreate(BaseModel):
    source: str = Field(..., min_length=3, max_length=255)
    destination: str = Field(..., min_length=3, max_length=255)
    active: bool = True


class AliasUpdate(BaseModel):
    destination: Optional[str] = Field(None, min_length=3, max_length=255)
    active: Optional[bool] = None


class AliasResponse(BaseModel):
    id: int
    source: str
    destination: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── DKIM ──────────────────────────────────────────────────
class DkimKeyCreate(BaseModel):
    selector: str = Field(default="mail", max_length=63)
    key_size: int = Field(default=2048, ge=1024, le=4096)


class DkimKeyResponse(BaseModel):
    id: int
    selector: str
    public_key: str
    key_size: int
    active: bool
    dns_record: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


# ── Settings ──────────────────────────────────────────────
class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    key: str
    value: str

    class Config:
        from_attributes = True


# ── Auth ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
