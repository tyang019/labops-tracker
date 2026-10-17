"""SQLAlchemy persistence models."""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Return an aware UTC timestamp for newly created records."""
    return datetime.now(timezone.utc)


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    asset_tag: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    serial_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    calibration_due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    test_runs: Mapped[list["TestRun"]] = relationship(back_populates="equipment")
    maintenance_tickets: Mapped[list["MaintenanceTicket"]] = relationship(
        back_populates="equipment"
    )


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), index=True)
    batch_id: Mapped[str] = mapped_column(String(80), index=True)
    measurement_value: Mapped[float] = mapped_column(Float)
    lower_spec_limit: Mapped[float] = mapped_column(Float)
    upper_spec_limit: Mapped[float] = mapped_column(Float)
    outcome: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    equipment: Mapped[Equipment] = relationship(back_populates="test_runs")


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), index=True)
    issue: Mapped[str] = mapped_column(String(500))
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance_tickets")
