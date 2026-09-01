# Architecture Notes

## Request lifecycle

1. A website form or n8n webhook submits a lead to `POST /api/leads`.
2. Pydantic validates contact fields, the service type and explicit consent.
3. The classifier scores service and message signals using visible rules.
4. The automation service assigns an owner and creates the CRM record.
5. A simulated notification and priority-based follow-up are stored.
6. The dashboard reads aggregate metrics and the latest pipeline records.

## Design choices

- **Explainable classification:** every priority includes a reason and score.
- **Replaceable services:** classification and automation logic live outside API routes.
- **Auditability:** each step writes an event to the lead timeline.
- **Honest demonstration:** notifications are marked simulated and seeded identities are fictional.
- **No invented outcomes:** dashboard timing is a configured routing target, not a client performance claim.
- **Low-friction setup:** SQLite and static assets keep the demo self-contained.

## Production upgrade path

| Demo component | Production option |
| --- | --- |
| SQLite | PostgreSQL with migrations and backups |
| Rule classifier | Hybrid rules plus an LLM behind the same interface |
| Simulated notification | Twilio, SendGrid or another consent-aware provider |
| Demo CRM tables | HubSpot, HighLevel, Jobber or Salesforce integration |
| Local process | Container hosting with health checks and observability |
| Single service | Queue-backed workers, retries and idempotency keys |

Authentication, role-based access, secrets management, rate limits and regional communication policies should be added before handling real leads.
