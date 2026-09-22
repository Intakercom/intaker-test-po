# Technical map

The application intentionally uses a small stack: a Python standard-library HTTP server, SQLite, and browser JavaScript. There are no package downloads or external calls at runtime.

## Request path

`frontend/app.js` → `/api/...` → `backend/server.py` → `Workshop` methods in `backend/service.py` → SQLite.

The server also serves `frontend/` so the UI and API share an origin. The default address is loopback only. The database lives in `data/` and is excluded from Git.

## Responsibilities

- `schema.sql`: tables, constraints, indexes, and relationships.
- `seed.py`: synthetic users and requests, stable references, and relative timestamps.
- `database.py`: connections, foreign keys, and first-run initialization.
- `service.py`: visibility, business actions, transactions, version checks, dashboard queries, imports, and the outbox simulator.
- `server.py`: routing, HTTP status codes, JSON validation, and static files.
- `app.js`: application state, rendering, filtering, forms, and API calls.
- `styles.css`: desktop and mobile presentation; no external fonts or asset CDN.

## Data groups

`organizations` and `users` provide workspace context. `requests` holds current repair information. `parts`, `activity`, and `messages` belong to requests. `imported_events` records processed form events.

Mutating an existing request uses its integer `version`. The UI sends the version it read; the backend rejects stale changes with HTTP 409. Failed operations roll back. Reload a request after a conflict before deciding how to retry.

Demo profiles are selected through `X-Demo-User`; the app has no passwords, login sessions, or real authorization identity. Within that demonstration model, the backend applies organization and role-based visibility. Changing the header impersonates another demo user by design.

## Intentional boundaries

The app is a functioning baseline with product limitations. It is not an unfinished implementation of the challenge solution. The live follow-up feature and take-home session planner do not exist yet. There is no hidden scheduling service, holiday calendar, real messaging provider, customer portal, or AI model call.

Tests and documentation can help you investigate. Verify the relevant implementation before treating a summary as proof. You do not need to inspect every file to complete either exercise.
