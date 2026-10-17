from tests.conftest import register_equipment


def test_maintenance_ticket_blocks_runs_and_resolution_restores_equipment(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    ticket_response = client.post("/maintenance-tickets", json={
        "equipment_id": equipment["id"],
        "issue": "Sensor readings are inconsistent",
        "priority": "high",
    })
    assert ticket_response.status_code == 201
    ticket = ticket_response.json()
    assert client.get(f"/equipment/{equipment['id']}").json()["status"] == "maintenance"

    blocked = client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-BLOCKED",
        "measurement_value": 10.0,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })
    assert blocked.status_code == 409

    resolved = client.patch(f"/maintenance-tickets/{ticket['id']}", json={"status": "resolved"})
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None
    assert client.get(f"/equipment/{equipment['id']}").json()["status"] == "available"


def test_dashboard_summary_counts_records(client, equipment_payload):
    equipment = register_equipment(client, equipment_payload)
    client.post("/test-runs", json={
        "equipment_id": equipment["id"],
        "batch_id": "BATCH-DASH",
        "measurement_value": 13.0,
        "lower_spec_limit": 8.0,
        "upper_spec_limit": 12.0,
    })
    summary = client.get("/dashboard/summary").json()
    assert summary["equipment_total"] == 1
    assert summary["equipment_available"] == 1
    assert summary["test_runs_total"] == 1
    assert summary["test_runs_failed"] == 1


def test_unknown_equipment_returns_not_found(client):
    response = client.get("/equipment/9999")
    assert response.status_code == 404
