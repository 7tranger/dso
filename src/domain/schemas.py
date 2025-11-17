from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CardColumn = Literal["backlog", "todo", "in_progress", "done"]


class ApiErrorPayload(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: str = "bearer"


class BoardBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=255)


class BoardCreate(BoardBase):
    pass


class BoardOut(BoardBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CardBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    column: CardColumn
    order_idx: int = Field(ge=0)
    estimate_hours: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), le=Decimal("1000")
    )
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned

    @field_validator("estimate_hours")
    @classmethod
    def normalize_estimate(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return None
        if not isinstance(value, Decimal):
            value = Decimal(value)
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("due_date")
    @classmethod
    def ensure_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class CardCreate(CardBase):
    board_id: int


class CardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    column: Optional[CardColumn] = None
    order_idx: Optional[int] = Field(default=None, ge=0)
    estimate_hours: Optional[Decimal] = Field(
        default=None, ge=Decimal("0"), le=Decimal("1000")
    )
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def strip_optional_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("title must not be empty")
        return cleaned

    @field_validator("estimate_hours")
    @classmethod
    def normalize_optional_estimate(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return None
        if not isinstance(value, Decimal):
            value = Decimal(value)
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("due_date")
    @classmethod
    def ensure_optional_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class CardMove(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column: CardColumn
    order_idx: int = Field(ge=0)


class CardOut(CardBase):
    id: int
    board_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context: Optional[str] = Field(default=None, max_length=1024)


class ScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: float
