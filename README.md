# Intake Desk

**A small community workshop. A second life for useful things.**

Intake Desk is a working, fictional repair-workshop application for a Technical Product Owner / Product Manager hiring exercise. Benchside Repair Collective repairs lamps, sewing machines, small appliances, and audio equipment.

Explore the product, investigate its code with AI, and propose improvements to its behavior and user experience. You are not expected to implement production code.

**New here? Start with [the candidate guide](CANDIDATE_README.md)** — it explains the three phases of the exercise and what we expect at each step.

This is an educational hiring scenario, separate from Intaker's commercial product. All people, records, organizations, and research evidence are fictional. The challenge does not ask you to solve an Intaker customer problem. Candidates retain ownership of their submitted work; it will be used for hiring assessment, not incorporated into a commercial product.

## Start in one command

You need **Python 3.11 or newer** and a modern browser. No packages, Node.js, Docker, database installation, API keys, or paid services are needed to run the application.

After cloning or downloading and extracting this repository, open a terminal **in the folder containing `run.py`**:

```sh
# macOS / Linux
python3 run.py
```

```powershell
# Windows
py -3 run.py
```

Open **http://127.0.0.1:8000**. The first run creates and seeds `data/workshop.sqlite3`. Edits persist when you restart. Press **Ctrl+C** in the terminal to stop.

If Python is not installed, download it from [python.org](https://www.python.org/downloads/). On Windows, the Python launcher (`py`) is convenient; `python run.py` also works if a supported Python is on your PATH. Check with `python3 --version` or `py -3 --version`.

### Reset or change the port

Stop every running copy of this app before resetting its data:

```sh
python3 run.py --reset
python3 run.py --port 8001
```

Use `py -3` in place of `python3` on Windows. Reset discards your local demo edits and restores the original fixtures. Do not reset a database while another instance is using it. Dates are relative to the reset time; request references stay the same.

## What works

- Create, search, and filter repair requests.
- Change priority, status, owner, and estimated repair time.
- Request a cost estimate approval and simulate the customer's decision.
- Record needed parts and move them through ordered / received states.
- Add workshop notes and inspect activity history.
- Queue customer updates, simulate provider acceptance or failure, and retry failures.
- Switch between coordinator and technician perspectives, or a second organization.
- Inspect a dashboard derived from current visible records.

**Nothing sends real email.** The provider simulator is a manual worker tick. This keeps the exercise deterministic and offline.

## Demo profiles

| Profile | Organization | Role |
|---|---|---|
| Alex Morgan | Benchside | Coordinator |
| Sam Rivera | Benchside | Technician; lighting and appliances |
| Jules Chen | Benchside | Technician; sewing and audio |
| Robin Ellis | Northstar | Coordinator at a different organization |

Use the profile selector in the top-right corner. The selector is deliberately simple demo infrastructure, not a real authentication system. Do not deploy this app on the public internet or enter real customer data.

## Find your way around

```text
run.py                    One-command startup, reset, and port selection
backend/
  schema.sql              Data model
  seed.py                 Fictional starting records
  service.py              Product rules, scoped queries, and simulated worker
  server.py               HTTP routes and frontend file serving
  database.py             SQLite setup and connections
frontend/
  index.html              App shell
  app.js                  UI rendering and API interactions
  styles.css              Responsive visual design
tests/test_workshop.py     Workflow, access, persistence, and HTTP tests
docs/                     Context and API / architecture orientation
challenges/               Candidate-facing briefs and submission outline
```

Read [the technical map](docs/TECHNICAL_MAP.md) and [API reference](docs/API.md) as needed. The code is the source of truth for current behavior. A proposed requirement is not evidence that the application already supports it.

## Run checks

```sh
python3 -m unittest discover -s tests -v
```

The suite uses temporary databases and an ephemeral local HTTP port. It never changes your demo database. On Windows, use `py -3 -m unittest discover -s tests -v`.

Frontend JavaScript is native browser JavaScript, with no build step. If Node.js is already installed, an optional syntax check is `node --check frontend/app.js`.

## Troubleshooting

| Problem | Fix |
|---|---|
| Command not found | Install Python 3.11+; try `python`, `python3`, or `py -3` as appropriate. |
| Port already in use | Stop the earlier instance or use `--port 8001`; open that port in the browser. |
| Page does not load | Keep the terminal running and use `http://127.0.0.1:8000`, not `https://` or a `file://` URL. |
| Repair disappeared | Check the selected profile, organization, search, category, and active/closed filter. |
| “This request has changed” | Another action updated the record. Refresh its drawer, review the new state, and reapply your change. |
| Want the original records | Stop the app, then run with `--reset`. |
| Corporate setup restriction | Tell the interviewer; setup problems are not part of the assessment. |

## Scope

This is a local hiring demo, not production software. Real login, real email, deployment infrastructure, customer self-service, session planning, calendar availability, and a scheduling engine are outside the baseline. See [LICENSE](LICENSE) for the application license. Interviewer scoring materials are distributed separately.
