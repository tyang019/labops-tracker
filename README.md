# LabOps Tracker

A Python portfolio project that simulates the sort of internal tooling a lab or medical-device production team might use to track equipment, test results, and maintenance work.

> **Scope note:** All equipment, batches, and measurements are fictional. This is a learning/demo application, not a validated quality-management system and not suitable for use in real medical-device production.

## What it demonstrates

- **Python fundamentals:** type hints, functions, structured modules, enums, exception handling, and clear separation of concerns.
- **REST API development:** FastAPI endpoints, request validation, response schemas, HTTP status codes, and generated OpenAPI documentation.
- **Data persistence:** SQLAlchemy models, relationships, SQLite, filtering, and aggregate queries.
- **Testability:** automated pytest tests for expected behavior, invalid inputs, failures, and cross-feature behavior.
- **Quality-oriented logic:** calculations are performed by the server; invalid specification ranges are rejected; overdue calibration and equipment under maintenance block new test runs.
- **Operational habits:** logging, a health endpoint, reproducible setup instructions, isolated test data, and GitHub Actions CI that runs tests on pushes and pull requests.

## Features

1. Register and search/filter lab equipment.
2. Record a simulated measurement with lower and upper specification limits. The API calculates `pass` or `fail`; the caller cannot submit an outcome directly.
3. Block test runs when equipment is under maintenance, retired, or past its calibration due date.
4. Open maintenance tickets, transition tickets through `open`, `in_progress`, and `resolved`, and return equipment to `available` only after active tickets are resolved.
5. View a dashboard summary of equipment, test runs, and active maintenance tickets.

## Requirements

- Python 3.11 or newer recommended
- pip

## Run locally on Windows PowerShell

From the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for an interactive API explorer. The local SQLite database (`labops.db`) is created in the project folder when the app starts.

## Run tests

In another PowerShell terminal, activate the same environment and run:

```powershell
python -m pytest -v
```

Tests use a separate in-memory SQLite database, so they do not use your local demo data.

## Suggested demo sequence

Use `/docs` in this order:

1. `POST /equipment` with an asset tag such as `LAB-001`, a serial number such as `SN-0001`, and a future calibration due date such as `2099-12-31`.
2. `POST /test-runs` with a measurement of `10`, lower limit `8`, and upper limit `12`. Confirm the response returns `pass`.
3. Submit a second run with measurement `13` and the same limits. Confirm the response returns `fail`.
4. `GET /dashboard/summary` to see the updated counts.
5. `POST /maintenance-tickets` for the equipment. Confirm its status becomes `maintenance` and a test run is rejected.
6. `PATCH /maintenance-tickets/{ticket_id}` with `{"status":"resolved"}`. Confirm the equipment returns to `available`.
7. Try invalid inputs, duplicate asset tags, or an overdue calibration date and explain why the API rejects them.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Basic service health check |
| POST | `/equipment` | Register equipment |
| GET | `/equipment` | List equipment; optionally filter with `?status=available` |
| GET | `/equipment/{equipment_id}` | Read one equipment record |
| POST | `/test-runs` | Record a simulated test and calculate pass/fail |
| GET | `/test-runs` | List test runs; optionally filter by `outcome` and `equipment_id` |
| POST | `/maintenance-tickets` | Open a maintenance ticket |
| PATCH | `/maintenance-tickets/{ticket_id}` | Move a ticket to `in_progress` or `resolved` |
| GET | `/maintenance-tickets` | List maintenance tickets; optionally filter with `?status=open` |
| GET | `/dashboard/summary` | Return aggregate counts |

## Design decisions and limitations

- The API calculates the test outcome server-side to avoid trusting a caller-provided result.
- The database enforces unique asset tags and serial numbers.
- Test runs are blocked if a device is not available or its calibration due date has passed.
- This starter version has no user accounts, audit-grade event history, electronic signatures, deployment hardening, or regulatory validation. These are intentionally out of scope for a beginner portfolio project.

## Possible next steps

- Add pagination and date-range filters.
- Add a CSV export for test history.
- Add a simple web dashboard.
- Add continuous integration with GitHub Actions to run tests on each push.
- Add a separate service layer and stronger audit logging if you can explain and test the extra complexity.
