from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.services.whatsapp_protocol import normalize_phone


class LinkWhatsApp(BaseModel):
    """Phone number to bind to the authenticated user."""

    phone: str = Field(..., examples=["5491112345678"])

    @field_validator("phone")
    @classmethod
    def normalize(cls, value: str) -> str:
        """Store digits only, matching the ``from`` field Meta sends."""
        phone = normalize_phone(value)
        if not 8 <= len(phone) <= 15:
            raise ValueError("phone must contain 8 to 15 digits")
        return phone


class WhatsAppLink(BaseModel):
    """Linked WhatsApp number for a user."""

    model_config = ConfigDict(from_attributes=True)

    phone: str
    user_id: int
