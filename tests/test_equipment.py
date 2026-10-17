from tests.conftest import register_equipment


def test_create_and_list_equipment(client, equipment_payload):
    created = client.post("/equipment", json=equipment_payload)
    assert created.status_code == 201
    assert created.json()["asset_tag"] == "LAB-001"
    assert created.json()["status"] == "available"

    listed = client.get("/equipment")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_duplicate_asset_tag_returns_conflict(client, equipment_payload):
    assert client.post("/equipment", json=equipment_payload).status_code == 201
    duplicate = {**equipment_payload, "serial_number": "SN-0002"}
    response = client.post("/equipment", json=duplicate)
    assert response.status_code == 409
    assert "unique" in response.json()["detail"]


def test_invalid_asset_tag_is_rejected(client, equipment_payload):
    equipment_payload["asset_tag"] = "bad tag with spaces"
    response = client.post("/equipment", json=equipment_payload)
    assert response.status_code == 422


def test_equipment_can_be_filtered_by_status(client, equipment_payload):
    register_equipment(client, equipment_payload)
    assert len(client.get("/equipment?status=available").json()) == 1
    assert client.get("/equipment?status=retired").json() == []
