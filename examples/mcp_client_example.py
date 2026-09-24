"""Example MCP client that calls list_characters on the character server.

From the host (Docker Compose running):

    docker compose up -d
    pip install 'mcp>=1.30,<2'   # only on the host, for this demo script
    python3 examples/mcp_client_example.py

Inside the API container (no extra host packages):

    docker compose exec character python examples/mcp_client_example.py
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _server_params(project_root: str) -> StdioServerParameters:
    """Run MCP in-container; from the host, reach it via ``docker compose exec``."""
    if os.path.isfile("/app/mcp_server.py"):
        return StdioServerParameters(
            command=sys.executable,
            args=["/app/mcp_server.py"],
            cwd="/app",
            env=os.environ.copy(),
        )

    compose_file = os.path.join(project_root, "docker-compose.yml")
    return StdioServerParameters(
        command="docker",
        args=[
            "compose",
            "-f",
            compose_file,
            "exec",
            "-i",
            "character",
            "python",
            "/app/mcp_server.py",
        ],
        cwd=project_root,
        env=os.environ.copy(),
    )


async def main() -> None:
    """Connect via stdio and invoke list_characters."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_params = _server_params(root)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])

            user_id = int(os.environ.get("MCP_DEFAULT_USER_ID", "1"))
            result = await session.call_tool(
                "list_characters",
                arguments={"user_id": user_id},
            )
            print("list_characters result:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
