from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SubjectInfo(BaseModel):
    community: str = Field(max_length=100)
    address: str = Field(default="", max_length=200)
    city: str = Field(default="", max_length=50)
    district: str = Field(default="", max_length=50)
    lng: float = Field(ge=73, le=136)
    lat: float = Field(ge=3, le=54)
    area: float = Field(gt=0)
    floor: int = Field(default=0, ge=0)
    total_floor: int = Field(default=0, ge=0)
    orientation: str = Field(default="", max_length=20)
    build_year: int = Field(default=0, ge=1900, le=2100)
    purpose: str = Field(default="住宅", max_length=30)


class ValuationTaskCreate(BaseModel):
    subject_info: SubjectInfo
    method: str = Field(default="comparison", pattern="^(comparison|income|cost)$")
    remark: str = Field(default="", max_length=2000)
    radius_m: int = Field(default=2000, ge=100, le=50000)
    max_comparables: int = Field(default=5, ge=1, le=20)


class AdjustmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comparable_id: int
    factor_scores: dict[str, Any]
    adjusted_price: float
    weight: float


class ValuationTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    subject_info: dict[str, Any]
    method: str
    result_price: float
    unit_price: float
    status: str
    remark: str
    created_at: datetime
    adjustments: list[AdjustmentOut] = []


class ValuationTaskListOut(BaseModel):
    total: int
    items: list[ValuationTaskOut]