"""Pydantic request and response schemas."""

import math
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EquipmentStatus(str, Enum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class TestOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class TicketPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class EquipmentCreate(BaseModel):
    asset_tag: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    serial_number: str = Field(min_length=2, max_length=80)
    calibration_due_date: date


class EquipmentRead(EquipmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: EquipmentStatus
    created_at: datetime


class TestRunCreate(BaseModel):
    equipment_id: int = Field(gt=0)
    batch_id: str = Field(min_length=1, max_length=80)
    measurement_value: float
    lower_spec_limit: float
    upper_spec_limit: float

    @field_validator("measurement_value", "lower_spec_limit", "upper_spec_limit")
    @classmethod
    def must_be_finite(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Measurement and specification limits must be finite numbers")
        return value

    @model_validator(mode="after")
    def validate_specification_range(self) -> "TestRunCreate":
        if self.lower_spec_limit >= self.upper_spec_limit:
            raise ValueError("lower_spec_limit must be less than upper_spec_limit")
        return self


class TestRunRead(TestRunCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    outcome: TestOutcome
    created_at: datetime


class MaintenanceTicketCreate(BaseModel):
    equipment_id: int = Field(gt=0)
    issue: str = Field(min_length=5, max_length=500)
    priority: TicketPriority = TicketPriority.NORMAL


class MaintenanceTicketUpdate(BaseModel):
    status: TicketStatus


class MaintenanceTicketRead(MaintenanceTicketCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TicketStatus
    created_at: datetime
    resolved_at: datetime | None


class DashboardSummary(BaseModel):
    equipment_total: int
    equipment_available: int
    equipment_in_maintenance: int
    test_runs_total: int
    test_runs_passed: int
    test_runs_failed: int
    maintenance_tickets_open: int
