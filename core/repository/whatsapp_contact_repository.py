from typing import Any, Callable, Optional

from sqlalchemy import select

from core.models.whatsapp_contact import WhatsAppContact


class WhatsAppContactRepository:
    """Persistence for WhatsApp phone → user links."""

    def __init__(self, session_factory: Callable[..., Any]):
        self.session_factory = session_factory

    async def find_by_phone(self, phone: str) -> Optional[WhatsAppContact]:
        """Return the link for a normalized phone, if any."""
        async with self.session_factory() as session:
            stmt = select(WhatsAppContact).where(WhatsAppContact.phone == phone)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int) -> Optional[WhatsAppContact]:
        """Return the link owned by ``user_id``, if any."""
        async with self.session_factory() as session:
            stmt = select(WhatsAppContact).where(WhatsAppContact.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def link(self, phone: str, user_id: int) -> WhatsAppContact:
        """Attach ``phone`` to ``user_id``, replacing any previous link for either side."""
        async with self.session_factory() as session:
            by_phone = await self._one(session, WhatsAppContact.phone == phone)
            by_user = await self._one(session, WhatsAppContact.user_id == user_id)

            if by_user is not None and by_phone is not None and by_user.id != by_phone.id:
                await session.delete(by_user)
                await session.flush()
                by_phone.user_id = user_id
                await session.commit()
                await session.refresh(by_phone)
                return by_phone

            if by_phone is not None:
                by_phone.user_id = user_id
                await session.commit()
                await session.refresh(by_phone)
                return by_phone

            if by_user is not None:
                by_user.phone = phone
                await session.commit()
                await session.refresh(by_user)
                return by_user

            entity = WhatsAppContact(phone=phone, user_id=user_id)
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def unlink_user(self, user_id: int) -> bool:
        """Delete the link for ``user_id``. Return whether a row was removed."""
        async with self.session_factory() as session:
            entity = await self._one(session, WhatsAppContact.user_id == user_id)
            if entity is None:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    @staticmethod
    async def _one(session, criterion) -> Optional[WhatsAppContact]:
        result = await session.execute(select(WhatsAppContact).where(criterion))
        return result.scalar_one_or_none()
