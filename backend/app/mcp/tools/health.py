from mcp.server.fastmcp import FastMCP

from app.services.health_service import get_health_status


def register_health_tools(server: FastMCP) -> None:
    @server.tool()
    def health_check() -> dict[str, str]:
        """Return the backend health status."""
        return get_health_status()
