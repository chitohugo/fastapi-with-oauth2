"""MCP server over Streamable HTTP (optional; for clients that avoid stdio)."""

from app.mcp.server import mcp


def main() -> None:
    """Run MCP on HTTP (default mount path /mcp)."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
