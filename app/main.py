"""LabOps Tracker: a demo API for simulated lab equipment and production checks.

All readings and equipment are fictional examples. This project is not intended
for use as a real medical-device quality system.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Equipment, MaintenanceTicket, TestRun
from app.schemas import (
    DashboardSummary,
    EquipmentCreate,
    EquipmentRead,
    EquipmentStatus,
    MaintenanceTicketCreate,
    MaintenanceTicketRead,
    MaintenanceTicketUpdate,
    TestOutcome,
    TestRunCreate,
    TestRunRead,
    TicketStatus,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("labops")

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize the local database tables when the API starts."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="LabOps Tracker API",
    description=(
        "A portfolio demo for tracking simulated lab equipment, test results, "
        "and maintenance tickets. It is not a validated medical-device system."
    ),
    version="1.0.0",
)

@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "application": "LabOps Tracker",
        "message": "Use /docs to explore the API.",
        "status": "running",
    }

@app.get("/test-runs/{test_run_id}", response_model=TestRunRead)
def get_test_run(
    test_run_id: int,
    db: Session = Depends(get_db),
) -> TestRun:
    test_run = db.get(TestRun, test_run_id)

    if test_run is None:
        raise HTTPException(
            status_code=404,
            detail="Test run not found",
        )

    return test_run

DbSession = Annotated[Session, Depends(get_db)]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/equipment", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate, db: DbSession) -> Equipment:
    equipment = Equipment(**payload.model_dump(), status=EquipmentStatus.AVAILABLE.value)
    db.add(equipment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.info("Rejected duplicate equipment identity for asset tag %s", payload.asset_tag)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="asset_tag and serial_number must both be unique",
        ) from exc
    db.refresh(equipment)
    logger.info("Registered equipment %s", equipment.asset_tag)
    return equipment


@app.get("/equipment", response_model=list[EquipmentRead])
def list_equipment(
    db: DbSession,
    equipment_status: Annotated[EquipmentStatus | None, Query(alias="status")] = None,
) -> list[Equipment]:
    query = select(Equipment).order_by(Equipment.asset_tag)
    if equipment_status is not None:
        query = query.where(Equipment.status == equipment_status.value)
    return list(db.scalars(query).all())


@app.get("/equipment/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, db: DbSession) -> Equipment:
    equipment = db.get(Equipment, equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment


@app.post("/test-runs", response_model=TestRunRead, status_code=status.HTTP_201_CREATED)
def create_test_run(payload: TestRunCreate, db: DbSession) -> TestRun:
    equipment = db.get(Equipment, payload.equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    if equipment.status != EquipmentStatus.AVAILABLE.value:
        raise HTTPException(status_code=409, detail="Equipment is not available for testing")
    if equipment.calibration_due_date < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=409, detail="Equipment calibration is overdue; test run blocked")

    outcome = (
        TestOutcome.PASS.value
        if payload.lower_spec_limit <= payload.measurement_value <= payload.upper_spec_limit
        else TestOutcome.FAIL.value
    )
    test_run = TestRun(**payload.model_dump(), outcome=outcome)
    db.add(test_run)
    db.commit()
    db.refresh(test_run)
    logger.info(
        "Recorded test run id=%s equipment_id=%s batch=%s outcome=%s",
        test_run.id,
        test_run.equipment_id,
        test_run.batch_id,
        test_run.outcome,
    )
    return test_run


@app.get("/test-runs", response_model=list[TestRunRead])
def list_test_runs(
    db: DbSession,
    outcome: TestOutcome | None = None,
    equipment_id: int | None = Query(default=None, gt=0),
) -> list[TestRun]:
    query = select(TestRun).order_by(TestRun.created_at.desc(), TestRun.id.desc())
    if outcome is not None:
        query = query.where(TestRun.outcome == outcome.value)
    if equipment_id is not None:
        query = query.where(TestRun.equipment_id == equipment_id)
    return list(db.scalars(query).all())


@app.post(
    "/maintenance-tickets",
    response_model=MaintenanceTicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_maintenance_ticket(payload: MaintenanceTicketCreate, db: DbSession) -> MaintenanceTicket:
    equipment = db.get(Equipment, payload.equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    if equipment.status == EquipmentStatus.RETIRED.value:
        raise HTTPException(status_code=409, detail="Retired equipment cannot receive maintenance tickets")

    ticket = MaintenanceTicket(**payload.model_dump(), status=TicketStatus.OPEN.value)
    equipment.status = EquipmentStatus.MAINTENANCE.value
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    logger.info("Opened maintenance ticket id=%s equipment_id=%s", ticket.id, equipment.id)
    return ticket


@app.patch("/maintenance-tickets/{ticket_id}", response_model=MaintenanceTicketRead)
def update_maintenance_ticket(
    ticket_id: int,
    payload: MaintenanceTicketUpdate,
    db: DbSession,
) -> MaintenanceTicket:
    ticket = db.get(MaintenanceTicket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Maintenance ticket not found")

    if ticket.status == TicketStatus.RESOLVED.value and payload.status != TicketStatus.RESOLVED:
        raise HTTPException(status_code=409, detail="Resolved tickets cannot be reopened in this demo")

    ticket.status = payload.status.value
    if payload.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.now(timezone.utc)
        active_tickets = db.scalars(
            select(MaintenanceTicket).where(
                MaintenanceTicket.equipment_id == ticket.equipment_id,
                MaintenanceTicket.id != ticket.id,
                MaintenanceTicket.status.in_([TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]),
            )
        ).all()
        equipment = db.get(Equipment, ticket.equipment_id)
        if equipment is not None and not active_tickets and equipment.status != EquipmentStatus.RETIRED.value:
            equipment.status = EquipmentStatus.AVAILABLE.value

    db.commit()
    db.refresh(ticket)
    logger.info("Updated maintenance ticket id=%s status=%s", ticket.id, ticket.status)
    return ticket


@app.get("/maintenance-tickets", response_model=list[MaintenanceTicketRead])
def list_maintenance_tickets(
    db: DbSession,
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
) -> list[MaintenanceTicket]:
    query = select(MaintenanceTicket).order_by(MaintenanceTicket.created_at.desc())
    if ticket_status is not None:
        query = query.where(MaintenanceTicket.status == ticket_status.value)
    return list(db.scalars(query).all())


@app.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: DbSession) -> DashboardSummary:
    equipment_total = db.scalar(select(func.count()).select_from(Equipment)) or 0
    equipment_available = db.scalar(
        select(func.count()).select_from(Equipment).where(Equipment.status == EquipmentStatus.AVAILABLE.value)
    ) or 0
    equipment_in_maintenance = db.scalar(
        select(func.count()).select_from(Equipment).where(Equipment.status == EquipmentStatus.MAINTENANCE.value)
    ) or 0
    test_runs_total = db.scalar(select(func.count()).select_from(TestRun)) or 0
    test_runs_passed = db.scalar(
        select(func.count()).select_from(TestRun).where(TestRun.outcome == TestOutcome.PASS.value)
    ) or 0
    test_runs_failed = db.scalar(
        select(func.count()).select_from(TestRun).where(TestRun.outcome == TestOutcome.FAIL.value)
    ) or 0
    maintenance_tickets_open = db.scalar(
        select(func.count()).select_from(MaintenanceTicket).where(
            MaintenanceTicket.status.in_([TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value])
        )
    ) or 0
    return DashboardSummary(
        equipment_total=equipment_total,
        equipment_available=equipment_available,
        equipment_in_maintenance=equipment_in_maintenance,
        test_runs_total=test_runs_total,
        test_runs_passed=test_runs_passed,
        test_runs_failed=test_runs_failed,
        maintenance_tickets_open=maintenance_tickets_open,
    )
