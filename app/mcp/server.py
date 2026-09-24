"""Entrypoint for the character MCP server (stdio transport)."""

from __future__ import annotations

import asyncio
import sys

from mcp.server.fastmcp import FastMCP
from sqlalchemy import text

from app.mcp.bootstrap import get_container
from app.mcp.tools import register_tools

mcp = FastMCP(
    "character-crud",
    instructions=(
        "Tools to manage Star Wars-style characters via the same service layer as the REST API. "
        "Pass user_id on each call or set MCP_DEFAULT_USER_ID in the server environment."
    ),
)

register_tools(mcp)


async def _verify_database_connection() -> None:
    """Fail fast with a clear error if the database is unreachable."""
    db = get_container().db()
    async with db.session() as session:
        await session.execute(text("SELECT 1"))


def main() -> None:
    """Run the MCP server on stdio."""
    try:
        asyncio.run(_verify_database_connection())
    except Exception as exc:
        print(
            "MCP startup failed: cannot connect to the database.\n"
            f"  {exc}\n"
            "If the API runs in Docker, run MCP inside the container (see .cursor/mcp.json) "
            "or set POSTGRES_HOST=localhost and POSTGRES_PORT=5434 on the host.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
