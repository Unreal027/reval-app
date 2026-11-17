from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Comparable(Base):
    __tablename__ = "comparables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    community: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str] = mapped_column(String(200), default="")
    city: Mapped[str] = mapped_column(String(50), default="", index=True)
    district: Mapped[str] = mapped_column(String(50), default="", index=True)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        Computed("ST_SetSRID(ST_MakePoint(lng, lat), 4326)", persisted=True),
        nullable=True,
    )
    area: Mapped[float] = mapped_column(Float)
    floor: Mapped[int] = mapped_column(Integer, default=0)
    total_floor: Mapped[int] = mapped_column(Integer, default=0)
    orientation: Mapped[str] = mapped_column(String(20), default="")
    build_year: Mapped[int] = mapped_column(Integer, default=0)
    deal_price: Mapped[float] = mapped_column(Float)
    deal_date: Mapped[date]
    source: Mapped[str] = mapped_column(String(100), default="")
    remark: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


Index("ix_comparables_location", Comparable.location, postgresql_using="gist")
