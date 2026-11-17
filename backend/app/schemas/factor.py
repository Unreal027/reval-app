from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FactorConfigCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(default="comparison", max_length=20)
    rules: dict[str, Any] = Field(default_factory=dict)
    remark: str = Field(default="", max_length=2000)


class FactorConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    rules: dict[str, Any]
    remark: str


class FactorConfigListOut(BaseModel):
    total: int
    items: list[FactorConfigOut]