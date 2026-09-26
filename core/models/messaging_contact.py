from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from core.models.base_model import Base


class MessagingContact(Base):
    """Channel identity (phone, chat id, ...) linked to the user who owns commands."""

    __tablename__ = "messaging_contacts"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_messaging_provider_external_id"),
        UniqueConstraint("provider", "user_id", name="uq_messaging_provider_user"),
    )

    provider = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
