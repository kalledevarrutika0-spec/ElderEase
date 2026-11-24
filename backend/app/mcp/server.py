from mcp.server.fastmcp import FastMCP

from app.mcp.tools.health import register_health_tools
from app.mcp.tools.refill import register_refill_tools

mcp_server = FastMCP("Elderease")
register_health_tools(mcp_server)
register_refill_tools(mcp_server)


if __name__ == "__main__":
    mcp_server.run(transport="stdio")
