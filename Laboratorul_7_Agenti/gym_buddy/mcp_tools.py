from agno.tools.mcp import MCPTools

base_url = "http://127.0.0.1:8300/mcp"

NUTRITION_TOOLS = MCPTools(
    url=f"{base_url}/nutrition/mcp",
    transport="streamable-http",
    refresh_connection=True,
    timeout_seconds=300,
)

WORKOUT_TOOLS = MCPTools(
    url=f"{base_url}/workout/mcp",
    transport="streamable-http",
    refresh_connection=True,
    timeout_seconds=300,
)
