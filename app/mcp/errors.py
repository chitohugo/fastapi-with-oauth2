"""Map domain errors to MCP tool errors."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from core.exceptions import BaseError
from mcp.server.fastmcp.exceptions import ToolError

T = TypeVar("T")


async def invoke_service(call: Callable[[], Awaitable[T]]) -> T:
    """Run an async service call and translate domain errors.

    Args:
        call: Zero-argument async callable that performs the service operation.

    Returns:
        The service call result.

    Raises:
        ToolError: When the service raises a ``BaseError``.
    """
    try:
        return await call()
    except BaseError as exc:
        raise ToolError(exc.message) from exc
