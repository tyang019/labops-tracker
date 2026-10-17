# Build Plan and Interview Talking Points

## Milestone 1: Understand and run the starter

- Set up a virtual environment, install dependencies, launch the API, and run every test.
- Read `schemas.py`, then `models.py`, then `main.py`.
- Explain the difference between a request schema (validation) and a database model (persistence).

## Milestone 2: Own the code

- Change one validation rule, add a test for it, and rerun the suite.
- Add a `GET /test-runs/{run_id}` endpoint with a 404 test.
- Add pagination to `GET /test-runs` using `limit` and `offset`, with bounds validation.

## Milestone 3: Demonstrate engineering practice

- Create a GitHub repository with a useful README and small commits.
- Review the included GitHub Actions workflow and confirm it passes after pushing to your own repository.
- Add a CSV export, then write tests for empty data and special characters.

## Be ready to explain

1. Why does the API calculate pass/fail rather than accept it from the caller?
2. What is the difference between HTTP 404, 409, and 422 in this project?
3. How do the tests avoid modifying the local demo database?
4. What happens if an instrument is past its calibration date?
5. How would you investigate an unexpected `500` response in a real application?
6. Why is this a simulation rather than a validated medical-device quality system?
