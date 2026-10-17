"""Shared fixtures using an isolated in-memory SQLite database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture()
def equipment_payload():
    return {
        "asset_tag": "LAB-001",
        "name": "Bench Pressure Sensor",
        "serial_number": "SN-0001",
        "calibration_due_date": "2099-12-31",
    }


def register_equipment(client: TestClient, payload: dict | None = None) -> dict:
    response = client.post("/equipment", json=payload or {
        "asset_tag": "LAB-001",
        "name": "Bench Pressure Sensor",
        "serial_number": "SN-0001",
        "calibration_due_date": "2099-12-31",
    })
    assert response.status_code == 201, response.text
    return response.json()
