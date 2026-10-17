from tests.conftest import register_equipment


def test_test_run_outcome_is_calculated_by_server(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    response = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-100",
        "measurement_value": 10.0,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })
    assert response.status_code == 201
    assert response.json()["outcome"] == "pass"




def test_test_run_can_be_retrieved_by_id(client, equipment_payload):
    # Arrange: create equipment
    equipment = register_equipment(client, equipment_payload)

    # Act: create a test run
    create_response = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-106",
        "measurement_value": 10.0,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })

    assert create_response.status_code == 201

    # Get the ID assigned to the new test run
    test_run_id = create_response.json()["id"]

    # Act: retrieve that test run by ID
    response = client.get(f"/test-runs/{test_run_id}")

    # Assert: the correct test run is returned
    assert response.status_code == 200
    assert response.json()["id"] == test_run_id
    assert response.json()["batch_id"] == "BATCH-106"
    assert response.json()["outcome"] == "pass"


def test_test_run_not_found_returns_404(client):
    response = client.get("/test-runs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Test run not found"




def test_out_of_range_measurement_fails(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    response = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-101",
        "measurement_value": 12.5,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })
    assert response.status_code == 201
    assert response.json()["outcome"] == "fail"


def test_invalid_specification_range_is_rejected(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    response = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-102",
        "measurement_value": 10.0,
        "lower_spec_limit": 12.0,
        "upper_spec_limit": 8.0,
    })
    assert response.status_code == 422


def test_overdue_calibration_blocks_test_run(client):
    equipment = register_equipment(client, {
        "asset_tag": "LAB-OLD",
        "name": "Overdue Sensor",
        "serial_number": "SN-OLD",
        "calibration_due_date": "2000-01-01",
    })
    response = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-103",
        "measurement_value": 10.0,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })
    assert response.status_code == 409
    assert "calibration is overdue" in response.json()["detail"]


def test_runs_can_be_filtered_by_outcome(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    base = {
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-104",
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    }
    assert client.post("/test-runs", json={**base, "measurement_value": 10.0}).status_code == 201
    assert client.post("/test-runs", json={**base, "batch_id": "BATCH-105", "measurement_value": 15.0}).status_code == 201
    assert len(client.get("/test-runs?outcome=pass").json()) == 1
    assert len(client.get("/test-runs?outcome=fail").json()) == 1
