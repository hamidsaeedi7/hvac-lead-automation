from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.database import (
    add_event,
    add_follow_up,
    add_notification,
    insert_lead,
    lead_count,
)
from app.models import LeadCreate
from app.services.classifier import classify_lead


FIRST_ACTION_SECONDS = {"urgent": 5, "high": 15, "normal": 30}
FOLLOW_UP_DELAYS = {
    "urgent": timedelta(minutes=10),
    "high": timedelta(hours=2),
    "normal": timedelta(hours=24),
}


def process_lead(payload: LeadCreate) -> dict:
    created_at = datetime.now(UTC)
    classification = classify_lead(payload.service_type, payload.message)
    lead_id = str(uuid4())
    follow_up_due = created_at + FOLLOW_UP_DELAYS[classification.priority]

    record = {
        "id": lead_id,
        "created_at": created_at.isoformat(),
        **payload.model_dump(),
        "priority": classification.priority,
        "score": classification.score,
        "reason": classification.reason,
        "assigned_to": classification.assigned_to,
        "status": classification.status,
        "recommended_actions": classification.recommended_actions,
        "first_action_seconds": FIRST_ACTION_SECONDS[classification.priority],
    }
    insert_lead(record)

    add_event(lead_id, "lead_captured", "Lead received from the website form.")
    add_event(
        lead_id,
        "classified",
        f"Priority set to {classification.priority}: {classification.reason}",
    )
    add_event(lead_id, "crm_upserted", "Lead record created in the demo CRM.")
    add_event(
        lead_id,
        "owner_assigned",
        f"Assigned to {classification.assigned_to}.",
    )

    if classification.priority == "urgent":
        notification_channel = "sms + email"
        message = (
            f"URGENT HVAC lead: {payload.full_name}, {payload.service_type}, "
            f"{payload.postal_code}. Call now: {payload.phone}"
        )
    else:
        notification_channel = payload.preferred_contact
        message = (
            f"New {classification.priority} HVAC lead: {payload.full_name}. "
            f"Next owner: {classification.assigned_to}."
        )

    add_notification(
        lead_id,
        notification_channel,
        classification.assigned_to,
        message,
    )
    add_event(
        lead_id,
        "notification_queued",
        f"Simulated {notification_channel} notification queued.",
    )

    template = (
        "Emergency callback check-in"
        if classification.priority == "urgent"
        else "Helpful booking and quote follow-up"
    )
    add_follow_up(
        lead_id,
        payload.preferred_contact,
        follow_up_due.isoformat(),
        template,
    )
    add_event(
        lead_id,
        "follow_up_scheduled",
        f"Follow-up scheduled for {follow_up_due.isoformat()}.",
    )

    return {
        "id": lead_id,
        "priority": classification.priority,
        "score": classification.score,
        "reason": classification.reason,
        "assigned_to": classification.assigned_to,
        "status": classification.status,
        "recommended_actions": classification.recommended_actions,
        "follow_up_due_at": follow_up_due.isoformat(),
        "simulated_notification": message,
    }


def seed_demo_data() -> None:
    if lead_count() > 0:
        return

    samples = [
        LeadCreate(
            full_name="Sarah Mitchell",
            email="sarah@example.com",
            phone="+1 613 555 0182",
            service_type="emergency_repair",
            postal_code="K1T 2N4",
            message="No heat since last night and there is a baby in the house.",
            preferred_contact="phone",
            consent=True,
        ),
        LeadCreate(
            full_name="Daniel Cooper",
            email="daniel@example.com",
            phone="+1 613 555 0117",
            service_type="air_conditioning",
            postal_code="K2J 4B7",
            message="The AC stopped working this afternoon. Please call when possible.",
            preferred_contact="sms",
            consent=True,
        ),
        LeadCreate(
            full_name="Emily Nguyen",
            email="emily@example.com",
            phone="+1 613 555 0144",
            service_type="installation_quote",
            postal_code="K2L 3W1",
            message="Looking for a heat pump quote for a detached home built in 1998.",
            preferred_contact="email",
            consent=True,
        ),
    ]
    for sample in samples:
        process_lead(sample)
