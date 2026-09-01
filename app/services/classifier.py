from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    priority: str
    score: int
    reason: str
    assigned_to: str
    status: str
    recommended_actions: list[str]


EMERGENCY_KEYWORDS = {
    "no heat": 5,
    "no heating": 5,
    "no cooling": 4,
    "gas smell": 8,
    "carbon monoxide": 10,
    "burning smell": 8,
    "sparking": 8,
    "water leak": 6,
    "leaking": 4,
    "frozen": 3,
    "stopped working": 4,
    "not working": 3,
    "baby": 2,
    "elderly": 2,
}

SERVICE_WEIGHTS = {
    "emergency_repair": 5,
    "furnace_repair": 2,
    "air_conditioning": 2,
    "heat_pump": 1,
    "water_heater": 2,
    "maintenance": 0,
    "installation_quote": 0,
    "indoor_air_quality": 1,
}


def classify_lead(service_type: str, message: str) -> Classification:
    normalized = message.lower().strip()
    score = SERVICE_WEIGHTS.get(service_type, 0)
    matched: list[str] = []

    for keyword, weight in EMERGENCY_KEYWORDS.items():
        if keyword in normalized:
            score += weight
            matched.append(keyword)

    if score >= 7:
        priority = "urgent"
        assigned_to = "Emergency Dispatch"
        status = "urgent_dispatch"
        actions = [
            "Call the lead within 5 minutes",
            "Confirm safety and equipment status",
            "Offer the earliest emergency window",
        ]
    elif score >= 4:
        priority = "high"
        assigned_to = "Service Coordinator"
        status = "qualified"
        actions = [
            "Review the request within 30 minutes",
            "Confirm service area and availability",
            "Send booking options",
        ]
    else:
        priority = "normal"
        assigned_to = "Comfort Advisor"
        status = "follow_up_scheduled"
        actions = [
            "Send a helpful acknowledgement",
            "Collect equipment and home details",
            "Schedule a quote or maintenance follow-up",
        ]

    if matched:
        reason = f"Matched urgency signals: {', '.join(matched[:3])}."
    elif service_type == "emergency_repair":
        reason = "Emergency repair was selected."
    elif service_type in {"furnace_repair", "air_conditioning", "water_heater"}:
        reason = "Repair request requires timely service coordination."
    else:
        reason = "No immediate safety or outage signal was detected."

    return Classification(
        priority=priority,
        score=score,
        reason=reason,
        assigned_to=assigned_to,
        status=status,
        recommended_actions=actions,
    )

