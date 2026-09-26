from typing import Any, Callable, Optional

from sqlalchemy import select

from core.models.messaging_contact import MessagingContact


class MessagingContactRepository:
    """Persistence for provider identity → user links."""

    def __init__(self, session_factory: Callable[..., Any]):
        self.session_factory = session_factory

    async def find_by_external_id(
        self,
        provider: str,
        external_id: str,
    ) -> Optional[MessagingContact]:
        """Return the link for this channel identity, if any."""
        async with self.session_factory() as session:
            return await self._one(session, provider, external_id=external_id)

    async def find_by_user(self, provider: str, user_id: int) -> Optional[MessagingContact]:
        """Return the user's link on this channel, if any."""
        async with self.session_factory() as session:
            return await self._one(session, provider, user_id=user_id)

    async def link(self, provider: str, external_id: str, user_id: int) -> MessagingContact:
        """Attach an identity to a user on one channel, replacing either previous link."""
        async with self.session_factory() as session:
            by_identity = await self._one(session, provider, external_id=external_id)
            by_user = await self._one(session, provider, user_id=user_id)

            if by_user is not None and by_identity is not None and by_user.id != by_identity.id:
                await session.delete(by_user)
                await session.flush()
                by_identity.user_id = user_id
                await session.commit()
                await session.refresh(by_identity)
                return by_identity

            if by_identity is not None:
                by_identity.user_id = user_id
                await session.commit()
                await session.refresh(by_identity)
                return by_identity

            if by_user is not None:
                by_user.external_id = external_id
                await session.commit()
                await session.refresh(by_user)
                return by_user

            entity = MessagingContact(provider=provider, external_id=external_id, user_id=user_id)
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def unlink(self, provider: str, user_id: int) -> bool:
        """Delete the user's link on this channel. Return whether a row was removed."""
        async with self.session_factory() as session:
            entity = await self._one(session, provider, user_id=user_id)
            if entity is None:
                return False
            await session.delete(entity)
            await session.commit()
            return True

    @staticmethod
    async def _one(
        session,
        provider: str,
        external_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Optional[MessagingContact]:
        stmt = select(MessagingContact).where(MessagingContact.provider == provider)
        if external_id is not None:
            stmt = stmt.where(MessagingContact.external_id == external_id)
        if user_id is not None:
            stmt = stmt.where(MessagingContact.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
