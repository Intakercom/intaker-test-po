# API reference

Base URL: `http://127.0.0.1:8000/api`. JSON writes use `Content-Type: application/json`. Select a demo persona with `X-Demo-User: alex`, `sam`, `jules`, or `robin`. The default is Alex.

| Method / path | Purpose |
|---|---|
| `GET /health` | Startup health check. |
| `GET /bootstrap` | Current user, organization, demo profiles, local staff and enum values. |
| `GET /requests` | Visible requests, owner names, and part counts. |
| `GET /requests/{id}` | One visible request with parts, activity, and messages. |
| `POST /requests` | Create an unassigned request. Coordinator only. |
| `PATCH /requests/{id}` | Change workflow fields. Include `version`. |
| `POST /requests/{id}/notes` | Add an internal note: `body`, `version`. |
| `POST /requests/{id}/parts` | Add a part: `name`, `quantity`, `version`. |
| `POST /requests/{id}/part-status` | Update part: `part_id`, `status`, `version`. |
| `POST /requests/{id}/quote` | Create/replace a quoted cost: `quote_cents`, `version`. Coordinator only. |
| `POST /requests/{id}/approval` | Simulate customer decision: `decision` (`approved` / `declined`), `version`. Coordinator only. |
| `POST /requests/{id}/messages` | Queue a simulated update: `body`, `version`. |
| `POST /requests/{id}/retry-message` | Requeue a failed update: `message_id`, `version`. |
| `GET /dashboard` | Counts computed from currently visible requests. |
| `GET /outbox` | Messages for visible requests. |
| `POST /outbox/process` | One provider simulation tick: `fail_first` boolean, default false. Coordinator only. |
| `POST /imports/dropoff` | Create from an external-form event; create fields plus `event_id`. Coordinator only. |

The import endpoint is a local simulation, not an authenticated public webhook.

## Create example

```json
{
  "customer_name": "Casey Example",
  "customer_email": "casey@example.test",
  "equipment": "Reading lamp",
  "category": "lighting",
  "description": "The switch needs attention.",
  "priority": "normal"
}
```

Categories: `lighting`, `sewing`, `appliances`, `audio`. Priority: `normal` or `high`.

## Workflow example

```json
{
  "version": 1,
  "status": "assessing",
  "assigned_to": "sam",
  "estimated_minutes": 45,
  "priority": "normal"
}
```

Only send the fields you intend to change. Coordinators can assign a technician or clear assignment with `null`, and can change priority. Technicians can update status and bench-time estimates on visible requests. An estimate may be `null` when unknown; otherwise it is an integer from 1 to 480 minutes. Cost estimates are integer pence from 0 to 100000.

Statuses: `new`, `assessing`, `queued`, `repairing`, `ready`, `closed`, `cancelled`.

## Errors

Errors return JSON: `{"error": "Human-readable explanation"}`.

- `400`: invalid input.
- `401`: unknown demo profile.
- `403`: action unavailable for this role, or invalid local-origin request.
- `404`: endpoint/resource not found or not visible.
- `409`: stale request version or action incompatible with current state.
- `413`: request body too large.
- `415`: JSON content type required.

No HTTP client is required for the interview. The UI and source are enough.
