
from __future__ import annotations
import asyncio
import json
import sys
import threading
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import Tool


# Path to the MCP server script
MCP_SERVER_PATH = Path(__file__).resolve().parent / "server.py"


class MCPClient:

    def __init__(self):
        self._tools: Optional[List[Tool]] = None
        self._sync_tools: Optional[List[Tool]] = None
        self._session = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._is_connected = False
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def connect(self) -> List[Tool]:
        # Return cached tools if already connected
        if self._is_connected and self._tools is not None:
            return self._tools

        try:
            from langchain_mcp_adapters.tools import load_mcp_tools
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(MCP_SERVER_PATH)],
            )

            # Use AsyncExitStack to properly manage context managers
            # within the same async task, avoiding cancel scope issues
            self._exit_stack = AsyncExitStack()
            read, write = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self._session.initialize()

            # Load tools via adapter
            self._tools = await load_mcp_tools(self._session)
            self._is_connected = True
            print("Connected to MCP server - %d tools loaded" % (len(self._tools)))
            return self._tools

        except Exception as e:
            print("MCP connection failed: %s - falling back to direct tools" % (e))
            return self._get_fallback_tools()

    async def disconnect(self) -> None:
        try:
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None
            self._session = None
            self._is_connected = False
        except Exception as e:
            print("Error disconnecting MCP: %s" % (e))

    def _get_fallback_tools(self) -> List[Tool]:
        from langchain_core.tools import StructuredTool
        from src.mcp.tools import inventory_lookup, carrier_rates

        def inventory_lookup_wrapper(skus: List[str], warehouse_id: Optional[str] = None) -> str:
            return json.dumps(inventory_lookup(skus=skus, warehouse_id=warehouse_id), indent=2)

        def carrier_rates_wrapper(total_weight_kg: float, destination_state: str, service_level: str = "standard", is_hazmat: bool = False, order_value: float = 0.0) -> str:
            return json.dumps(
                carrier_rates(
                    total_weight_kg=total_weight_kg,
                    destination_state=destination_state,
                    service_level=service_level,
                    is_hazmat=is_hazmat,
                    order_value=order_value,
                ),
                indent=2,
            )

        tools = [
            StructuredTool.from_function(
                name="inventory_lookup",
                description="Look up inventory levels for given SKUs across warehouses.",
                func=inventory_lookup_wrapper,
            ),
            StructuredTool.from_function(
                name="carrier_rates",
                description="Get carrier rates and eligibility for given shipment parameters.",
                func=carrier_rates_wrapper,
            ),
        ]
        print("Using %d fallback tools (direct implementation)", len(tools))
        return tools

    def get_tools_sync(self) -> List[Tool]:
        # Return cached sync tools if available
        if self._sync_tools is not None:
            return self._sync_tools

        try:
            mcp_tools = asyncio.run_coroutine_threadsafe(self.connect(), self._loop).result()
            
            sync_tools = []
            from langchain_core.tools import StructuredTool
            for t in mcp_tools:
                def make_sync_func(tool_instance):
                    def _sync_func(*args, **kwargs):
                        coro = tool_instance.ainvoke(args[0] if args else kwargs)
                        result = asyncio.run_coroutine_threadsafe(coro, self._loop).result()
                        # Extract text from list of TextContent objects to match standard tool behavior
                        if isinstance(result, list):
                            return "\n".join(getattr(item, "text", str(item)) for item in result)
                        return str(result) if not isinstance(result, str) else result
                    return _sync_func

                sync_tools.append(
                    StructuredTool(
                        name=t.name,
                        description=t.description,
                        args_schema=t.args_schema,
                        func=make_sync_func(t),
                    )
                )
            
            self._sync_tools = sync_tools
            return sync_tools
        except Exception as e:
            print("Sync MCP connection failed: %s" % (e))
            return self._get_fallback_tools()


_mcp_client = None

def get_mcp_tools() -> List[Tool]:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client.get_tools_sync()
