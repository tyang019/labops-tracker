
# LabOps Tracker

LabOps Tracker is a Python API that simulates an internal application for tracking laboratory equipment, test measurements, and maintenance activities.

> **Scope note:** All equipment, batches, and measurements are fictional. This is a learning and demonstration project, not a validated quality-management system, and it is not suitable for use in real medical-device production.

## Features

- Register equipment and list records with optional status filtering.
- Record simulated batch measurements and calculate pass/fail outcomes from specification limits.
- Track calibration due dates and prevent test runs when equipment is overdue for calibration or unavailable.
- Create maintenance tickets and update their status.
- View dashboard summaries of equipment, test runs, and maintenance activity.
- Validate requests and return appropriate HTTP status codes for invalid requests and missing records.

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- pytest
- GitHub Actions

## Requirements

- Python 3.11 or newer
- pip

## Run Locally on Windows

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore and interact with the API.

The application creates a local SQLite database named `labops.db` in the project folder when it starts.

## Run Tests

With the virtual environment activated, run:

```powershell
python -m pytest -v
```

The automated tests use a separate in-memory SQLite database, keeping test records isolated from the local application database.

## Example Walkthrough

Use the interactive API documentation at `/docs` to try these operations:

1. Register equipment through `POST /equipment`, using an asset tag such as `LAB-001` and a future calibration due date.
2. Submit a test run through `POST /test-runs` with measurement `10`, lower limit `8`, and upper limit `12`. Verify that the calculated outcome is `pass`.
3. Submit another test run with measurement `13` and the same limits. Verify that the outcome is `fail`.
4. Retrieve an individual test run through `GET /test-runs/{test_run_id}`.
5. View updated totals through `GET /dashboard/summary`.
6. Open a maintenance ticket and verify that equipment under maintenance cannot be used for new test runs.
7. Resolve the maintenance ticket and verify that the equipment becomes available when all active tickets have been resolved.
8. Try invalid inputs, duplicate asset tags, and overdue calibration dates to observe the API's validation and error responses.

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check service health |
| POST | `/equipment` | Register equipment |
| GET | `/equipment` | List and filter equipment |
| GET | `/equipment/{equipment_id}` | Retrieve one equipment record |
| POST | `/test-runs` | Create a test run and calculate its outcome |
| GET | `/test-runs` | List and filter test runs |
| GET | `/test-runs/{test_run_id}` | Retrieve one test run |
| POST | `/maintenance-tickets` | Open a maintenance ticket |
| PATCH | `/maintenance-tickets/{ticket_id}` | Update a maintenance ticket |
| GET | `/maintenance-tickets` | List and filter maintenance tickets |
| GET | `/dashboard/summary` | Retrieve dashboard totals |

## Design Decisions and Limitations

- Test outcomes are calculated by the server rather than accepted from the API caller.
- Asset tags and serial numbers must be unique.
- New test runs are blocked when equipment is unavailable or its calibration due date has passed.
- Automated tests use isolated database state to avoid relying on local demo records.

This project does not implement user accounts, audit-grade event history, electronic signatures, production deployment hardening, or regulatory validation. It is intended for learning and demonstration purposes.

## Potential Future Improvements

- Add pagination and date-range filters.
- Add CSV export for test history.
- Build a web dashboard for viewing equipment and test results.
- Explore stronger audit logging and additional automated tests.
