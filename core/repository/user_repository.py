from typing import Any, Callable

from core.models.user import User
from core.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, User)
