from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ComparableCreate(BaseModel):
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
    deal_price: float = Field(gt=0)
    deal_date: date
    source: str = Field(default="", max_length=100)
    remark: str = Field(default="", max_length=2000)


class ComparableOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    community: str
    address: str
    city: str
    district: str
    lng: float
    lat: float
    area: float
    floor: int
    total_floor: int
    orientation: str
    build_year: int
    deal_price: float
    deal_date: date
    source: str
    remark: str


class ComparableListOut(BaseModel):
    total: int
    items: list[ComparableOut]


class NearbyQuery(BaseModel):
    lng: float
    lat: float
    radius_m: int = Field(default=2000, ge=100, le=50000)
    limit: int = Field(default=20, ge=1, le=100)


class ComparableImportResult(BaseModel):
    inserted: int
    skipped: int
    errors: list[str] = []
