import os
from agno.tools.mcp import MCPTools, StreamableHTTPClientParams

from datetime import timedelta

base_url = "http://127.0.0.1:8200/mcp"


PERSONAL_ASSISTANT_TOOLS = MCPTools(
    url=f"{base_url}/personal/mcp",
    transport="streamable-http",
    refresh_connection=True,
    timeout_seconds=300,
)

COLLEGE_BUDDY_TOOLS = MCPTools(
    url=f"{base_url}/college/mcp",
    transport="streamable-http",
    refresh_connection=True,
    timeout_seconds=300,
)


