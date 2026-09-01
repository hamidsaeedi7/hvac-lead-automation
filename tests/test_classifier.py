from app.services.classifier import classify_lead


def test_emergency_lead_is_urgent():
    result = classify_lead(
        "emergency_repair",
        "No heat and there is a burning smell near the furnace.",
    )
    assert result.priority == "urgent"
    assert result.assigned_to == "Emergency Dispatch"
    assert result.score >= 7


def test_quote_lead_is_normal():
    result = classify_lead(
        "installation_quote",
        "I would like a quote for a new heat pump next month.",
    )
    assert result.priority == "normal"
    assert result.assigned_to == "Comfort Advisor"


def test_repair_signal_is_high_or_urgent():
    result = classify_lead(
        "air_conditioning",
        "The AC stopped working this afternoon.",
    )
    assert result.priority in {"high", "urgent"}
    assert "stopped working" in result.reason

