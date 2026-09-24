import json
import logging


class BaseError(Exception):
    """Base application error mapped to HTTP responses."""

    status_code: int = 500
    code: str = "internal_error"
    description: str = "Internal server error"

    def __init__(self, message: str, context=None, level=logging.ERROR):
        self.message = message
        super().__init__(message)
        log_content = {"message": message, "context": context}
        try:
            json.dumps(log_content)
        except Exception:
            pass


class AuthError(BaseError):
    status_code = 401
    code = "auth_error"
    description = "Authentication failed"


class ForbiddenError(BaseError):
    status_code = 403
    code = "forbidden"
    description = "You do not have permission to access this resource"


class NotFoundError(BaseError):
    status_code = 404
    code = "not_found"
    description = "Resource not found"


class DuplicatedError(BaseError):
    status_code = 409
    code = "duplicated"
    description = "The value already exists"
