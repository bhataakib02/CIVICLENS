"""Admin module — operational console backend."""
from app.modules.admin.router import admin_ops_router, agent_ops_router

__all__ = ["admin_ops_router", "agent_ops_router"]
