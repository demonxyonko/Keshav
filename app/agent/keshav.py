from typing import Any, Dict, List, Optional

from pydantic import Field, PrivateAttr

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.logger import logger
from app.prompt.keshav import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.mcp import MCPClients, MCPClientTool
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor


class KeshavAgent(ToolCallAgent):
    """General-purpose Keshav agent with local and MCP tools."""

    name: str = "Keshav"

    description: str = (
        "Keshav is a practical AI companion that can reason, "
        "use tools, browse, edit files, and complete multi-step tasks."
    )

    system_prompt: str = SYSTEM_PROMPT.format(
        directory=config.workspace_root
    )
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 5

    mcp_clients: MCPClients = Field(
        default_factory=MCPClients
    )

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            BrowserUseTool(),
            StrReplaceEditor(),
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(
        default_factory=lambda: [
            Terminate().name
        ]
    )

    browser_context_helper: Optional[Any] = Field(
        default=None,
        exclude=True,
    )

    connected_servers: Dict[str, str] = Field(
        default_factory=dict
    )

    _initialized: bool = PrivateAttr(
        default=False
    )
    _browser_helper_unavailable: bool = PrivateAttr(
        default=False
    )

    @classmethod
    async def create(
        cls,
        **kwargs,
    ) -> "KeshavAgent":
        """Create and initialize a KeshavAgent instance."""

        instance = cls(**kwargs)
        await instance.initialize_mcp_servers()
        instance._initialized = True
        return instance

    def _get_browser_context_helper(
        self,
    ) -> Optional[Any]:
        """
        Load BrowserContextHelper only when browser context is needed.

        The browser agent module also imports optional sandbox support.
        Keeping this import lazy allows KeshavAgent to work without
        Daytona installed.
        """

        if self.browser_context_helper is not None:
            return self.browser_context_helper

        if self._browser_helper_unavailable:
            return None

        try:
            from app.agent.browser import (
                BrowserContextHelper,
            )

        except ModuleNotFoundError as exc:
            if exc.name == "daytona":
                self._browser_helper_unavailable = True
                logger.warning(
                    "Optional Daytona package is not installed. "
                    "Sandbox browser context support is disabled."
                )
                return None

            raise

        self.browser_context_helper = (
            BrowserContextHelper(self)
        )

        return self.browser_context_helper

    async def initialize_mcp_servers(
        self,
    ) -> None:
        """Connect to configured MCP servers."""

        for (
            server_id,
            server_config,
        ) in config.mcp_config.servers.items():
            try:
                if (
                    server_config.type == "sse"
                    and server_config.url
                ):
                    await self.connect_mcp_server(
                        server_config.url,
                        server_id,
                    )
                    logger.info(
                        "Connected to MCP server "
                        f"{server_id} at "
                        f"{server_config.url}"
                    )

                elif (
                    server_config.type == "stdio"
                    and server_config.command
                ):
                    await self.connect_mcp_server(
                        server_config.command,
                        server_id,
                        use_stdio=True,
                        stdio_args=server_config.args,
                    )
                    logger.info(
                        "Connected to MCP server "
                        f"{server_id} using command "
                        f"{server_config.command}"
                    )

            except Exception as exc:
                logger.error(
                    "Failed to connect to MCP server "
                    f"{server_id}: {exc}"
                )

    async def connect_mcp_server(
        self,
        server_url: str,
        server_id: str = "",
        use_stdio: bool = False,
        stdio_args: Optional[List[str]] = None,
    ) -> None:
        """Connect to one MCP server and register its tools."""

        if use_stdio:
            await self.mcp_clients.connect_stdio(
                server_url,
                stdio_args or [],
                server_id,
            )
            self.connected_servers[
                server_id or server_url
            ] = server_url

        else:
            await self.mcp_clients.connect_sse(
                server_url,
                server_id,
            )
            self.connected_servers[
                server_id or server_url
            ] = server_url

        new_tools = [
            tool
            for tool in self.mcp_clients.tools
            if tool.server_id == server_id
        ]

        self.available_tools.add_tools(
            *new_tools
        )

    async def disconnect_mcp_server(
        self,
        server_id: str = "",
    ) -> None:
        """Disconnect an MCP server and remove its tools."""

        await self.mcp_clients.disconnect(
            server_id
        )

        if server_id:
            self.connected_servers.pop(
                server_id,
                None,
            )
        else:
            self.connected_servers.clear()

        base_tools = [
            tool
            for tool in self.available_tools.tools
            if not isinstance(
                tool,
                MCPClientTool,
            )
        ]

        self.available_tools = ToolCollection(
            *base_tools
        )
        self.available_tools.add_tools(
            *self.mcp_clients.tools
        )

    async def cleanup(self) -> None:
        """Clean up Keshav agent resources."""

        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()

        if self._initialized:
            await self.disconnect_mcp_server()
            self._initialized = False

    async def think(self) -> bool:
        """Decide the next action using the current context."""

        if not self._initialized:
            await self.initialize_mcp_servers()
            self._initialized = True

        original_prompt = self.next_step_prompt

        recent_messages = (
            self.memory.messages[-3:]
            if self.memory.messages
            else []
        )

        browser_in_use = any(
            tool_call.function.name
            == BrowserUseTool().name
            for message in recent_messages
            if message.tool_calls
            for tool_call in message.tool_calls
        )

        if browser_in_use:
            helper = (
                self._get_browser_context_helper()
            )

            if helper is not None:
                self.next_step_prompt = (
                    await helper
                    .format_next_step_prompt()
                )

        try:
            return await super().think()

        finally:
            self.next_step_prompt = (
                original_prompt
            )
