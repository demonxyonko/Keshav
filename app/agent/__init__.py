from importlib import import_module
from typing import Any


_AGENT_IMPORTS = {
    "BaseAgent": ("app.agent.base", "BaseAgent"),
    "BrowserAgent": ("app.agent.browser", "BrowserAgent"),
    "MCPAgent": ("app.agent.mcp", "MCPAgent"),
    "ReActAgent": ("app.agent.react", "ReActAgent"),
    "SWEAgent": ("app.agent.swe", "SWEAgent"),
    "ToolCallAgent": ("app.agent.toolcall", "ToolCallAgent"),
    "KeshavAgent": ("app.agent.keshav", "KeshavAgent"),
}


__all__ = list(_AGENT_IMPORTS)


def __getattr__(name: str) -> Any:
    """Load agent classes only when they are actually requested."""

    if name not in _AGENT_IMPORTS:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )

    module_name, class_name = _AGENT_IMPORTS[name]
    module = import_module(module_name)
    value = getattr(module, class_name)

    globals()[name] = value
    return value
