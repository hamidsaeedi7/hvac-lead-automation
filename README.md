# HVAC Lead Response & Follow-Up Automation

A working portfolio demo that turns an HVAC inquiry into a classified, assigned and scheduled CRM record.

The project is intentionally transparent: it uses sample data, explainable rules and simulated notifications. It does not claim production deployment or client results.

## Live interactive demo

[Open the HVAC LeadFlow demo](https://hamidsaeedi7.github.io/hvac-lead-automation/)

The public GitHub Pages preview mirrors the lead classification and routing flow safely in the browser. Test data is stored locally and no real email, SMS or API request is sent. The repository also includes the complete FastAPI, SQLite, Docker, automated test and n8n workflow implementation.

## What it demonstrates

- Responsive lead-capture experience
- Explainable urgency classification
- Priority-based team assignment
- CRM-style SQLite storage
- Event timeline for every automated step
- Simulated email/SMS alerts
- Priority-based follow-up scheduling
- Live metrics and lead pipeline dashboard
- Importable n8n webhook workflow
- FastAPI documentation at `/docs`

## Workflow

```text
Website form / n8n webhook
        -> validate and normalize
        -> classify urgency
        -> create CRM record
        -> assign owner
        -> simulate notification
        -> schedule follow-up
        -> update dashboard
```

## Architecture

| Layer | Responsibility |
| --- | --- |
| FastAPI | Validation, REST endpoints and static dashboard delivery |
| Rule classifier | Explainable urgency scoring and recommended actions |
| SQLite | CRM-like leads, events, notifications and follow-ups |
| Browser dashboard | Lead capture, live metrics, output and pipeline views |
| n8n workflow | Optional webhook entry point and API orchestration |

See `docs/architecture.md` for component boundaries and production upgrade paths.

## Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

The app creates `data/hvac_demo.db` and seeds three fictional demo leads on the first run.

## Run with Docker

```bash
docker compose up --build api
```

To run the optional n8n container as well:

```bash
docker compose --profile automation up --build
```

Then open:

- Demo: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- n8n: `http://127.0.0.1:5678`

Import `n8n/workflows/hvac-lead-response.json` into n8n and activate the webhook workflow.

## API example

```bash
curl -X POST http://127.0.0.1:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alex Morgan",
    "email": "alex@example.com",
    "phone": "+1 613 555 0199",
    "service_type": "emergency_repair",
    "postal_code": "K1V 8T7",
    "message": "No heat since last night and there is a baby in the house.",
    "preferred_contact": "phone",
    "consent": true
  }'
```

## Tests

```bash
pytest -q
```

## Production extension points

- Replace SQLite with PostgreSQL.
- Replace the rule classifier with an AI provider behind the same service interface.
- Connect HubSpot, HighLevel, Salesforce or another CRM through n8n/API calls.
- Connect Twilio, SendGrid or a regional messaging provider.
- Add authentication, role-based access and audit retention.
- Add idempotency keys, retries and a dead-letter queue.
- Add consent records and regional communication policies.

## Portfolio disclosure

This repository is a working concept demo created by Hamid Saeedi to demonstrate AI-ready automation architecture for service businesses. All people and contact details in seeded data are fictional.

For a concise walkthrough, use `docs/demo-script.md`.
