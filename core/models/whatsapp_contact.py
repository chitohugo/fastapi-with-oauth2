from sqlalchemy import Column, ForeignKey, Integer, String

from core.models.base_model import Base


class WhatsAppContact(Base):
    """Phone number linked to the user that owns WhatsApp commands."""

    __tablename__ = "whatsapp_contacts"

    phone = Column(String, unique=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
