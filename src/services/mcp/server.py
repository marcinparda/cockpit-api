from mcp.server.fastmcp import FastMCP
from redis.asyncio import Redis

from src.services.mcp.tools.budget import register_budget_tools
from src.services.mcp.tools.tasks import register_task_tools
from src.services.mcp.tools.cv import register_cv_tools
from src.services.mcp.tools.brain import register_brain_tools
from src.services.mcp.tools.hermes import register_hermes_tools
from src.services.mcp.resources.brain import register_brain_resources

redis_client: Redis | None = None

mcp = FastMCP("cockpit")

register_budget_tools(mcp)
register_task_tools(mcp)
register_cv_tools(mcp)
register_brain_tools(mcp)
register_hermes_tools(mcp)
register_brain_resources(mcp)

mcp_asgi = mcp.streamable_http_app()
