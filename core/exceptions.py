from typing import Any, Dict, Optional

from abc import ABC, abstractmethod
import json
import logging


class BaseError(Exception, ABC):
    """Class to subclass by different exception classes."""

    @property
    @abstractmethod
    def code(self):
        """Represent the error with a custom code."""
        ...

    @property
    @abstractmethod
    def description(self):
        """Represent the error description."""
        ...

    def __init__(self, message, context=None, level=logging.ERROR):
        """Initialize class.

        Parameters
        ----------
        message : str
            descriptive error message.
        context : can be converted to string
            info to be logged relative to the error.
        """
        self.message = message
        log_content = {
            "message": message,
            "context": context
        }
        try:
            log_content = json.dumps(log_content)
        except Exception:
            log_content = {"message": message}

class AuthError(BaseError):
    def __init__(self, message) -> None:
        ...

class HTTPError(BaseError):
    """Class to subclass by different exception classes."""

    @property
    @abstractmethod
    def status_code(self, message):
        """Represent the HTTPStatus value of the error."""
        ...


class DuplicatedError(BaseError):
    def __init__(self, message) -> None:
        ...

class AuthError(BaseError):
    def __init__(self, message) -> None:
        ...

class NotFoundError(BaseError):
    def __init__(self, message) -> None:
        ...