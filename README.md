# Backend Project

A Flask API with registration, JWT login, user profiles, and private user-owned records.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and replace both secret values with long random values.
4. Create/update the database schema: `flask --app run_dev db upgrade`
5. Start the API: `python run_dev.py`

The local development server listens on `http://127.0.0.1:5002`.

## Ownership protection

- `backend_project_app/auth.py` contains `login_required`, which validates a JWT and loads the authenticated `User` into `g.current_user`.
- The same file contains `require_record_owner`, which compares the record's `owner_id` with the authenticated user's database ID and returns 403 when they differ.
- `backend_project_app/main.py` applies the decorator to the record routes and calls the ownership helper before reading, updating, or deleting a single record.
- `POST /records` always sets `owner_id` from `g.current_user.id`; it never trusts an `owner_id` sent by the client.
- `GET /records` filters by the authenticated user's ID, so users only receive their own records.

Responses: 401 means missing/invalid authentication; 403 means authenticated but not the owner; 404 means the requested record does not exist.

## Record API

All record endpoints require `Authorization: Bearer <token>`.

- `GET /records` — list the current user's records
- `POST /records` — create a record (`{"title":"My record","content":"Private text"}`)
- `GET /records/<id>` — read one owned record
- `PUT /records/<id>` — update an owned record
- `DELETE /records/<id>` — delete an owned record

## Database configuration and Docker Compose

`config.py` reads `DATABASE_URL` from the environment. Development uses `sqlite:///development.db` if the variable is not set. Production uses the supplied `DATABASE_URL`; it does not hardcode a live database address.

`compose.yaml` passes the host's `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET` into the web container. Set those variables in the environment where Docker Compose runs (or in a local `.env` file that is not committed). For example, `DATABASE_URL` should be the connection string supplied by the live database host. The exact value depends on the database provider and is intentionally not included in source control.

Run with Docker Compose after setting those three environment variables:

```sh
docker compose up --build
```

For a new or existing database whose Alembic history is already at the current head, apply the new records migration with:

```sh
flask --app run_dev db upgrade
```

If you have a database that has never been migrated, the normal initial setup is to apply the full migration history with the same command. Back up any production database before applying migrations.

## Design decision

The app uses a Flask application factory (`create_app`) and separates extensions, models, authentication helpers, routes, and configuration. This was chosen over one large module with a global Flask app because it makes the application easier to test under different configurations and keeps authentication/authorization logic reusable. Database addresses and secrets are supplied through environment configuration rather than committed in code, allowing the same codebase to run locally and on a hosted database.
