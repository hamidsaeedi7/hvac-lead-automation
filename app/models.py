from typing import Literal
import re

from pydantic import BaseModel, Field, field_validator


ServiceType = Literal[
    "emergency_repair",
    "furnace_repair",
    "air_conditioning",
    "heat_pump",
    "water_heater",
    "maintenance",
    "installation_quote",
    "indoor_air_quality",
]


class LeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    phone: str = Field(min_length=7, max_length=32)
    service_type: ServiceType
    postal_code: str = Field(min_length=3, max_length=16)
    message: str = Field(min_length=5, max_length=1500)
    preferred_contact: Literal["phone", "email", "sms"] = "phone"
    consent: bool

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        digits = re.sub(r"\D", "", value)
        if len(digits) < 7:
            raise ValueError("Enter a valid phone number")
        return value

    @field_validator("postal_code", "full_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class LeadCreated(BaseModel):
    id: str
    priority: Literal["urgent", "high", "normal"]
    score: int
    reason: str
    assigned_to: str
    status: str
    recommended_actions: list[str]
    follow_up_due_at: str
    simulated_notification: str


class DashboardStats(BaseModel):
    total: int
    urgent: int
    high: int
    normal: int
    open_follow_ups: int
    simulated_messages: int
    average_routing_target_seconds: float
