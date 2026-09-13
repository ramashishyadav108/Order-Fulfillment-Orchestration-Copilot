
from __future__ import annotations
import json
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole
from src.models.inventory import AllocationResult, AllocationStatus
from src.models.fulfillment import FulfillmentStatus
from src.mcp.client import get_mcp_tools



class InventoryAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.INVENTORY, **kwargs)
        # Load MCP tools - falls back to direct implementation on failure
        all_tools = get_mcp_tools()
        self.inv_tool = next((t for t in all_tools if t.name == "inventory_lookup"), None)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        order = state.get("order") or {}
        order_id = order.get("order_id", "unknown")
        skus = order.get("item_skus", [])
        print("InventoryAgent: order=%s, SKUs=%s" % (order_id, skus))

# ── Step 1: Call MCP tool for raw inventory data
        tool_result = "{}"
        if self.inv_tool and skus:
            try:
                tool_input = {"skus": skus}
                tool_result = self.inv_tool.invoke(tool_input)
                print("InventoryAgent: MCP tool returned %d chars" % (len(tool_result)))
            except Exception as e:
                print("InventoryAgent: MCP tool failed: %s" % (e))
                tool_result = json.dumps({"error": str(e)})
        else:
            print("InventoryAgent: no inventory_lookup tool or empty SKU list")

# ── Step 2: LLM decides allocation based on tool data
        context = self.context_manager.prepare_agent_context(
            self.role, state.get("context") or {}
        )
        context_str = self.context_manager.context_to_prompt(context)

        prompt = f"""
You are the Inventory Allocation Agent.

{context_str}

Inventory data (from MCP inventory_lookup tool):
{tool_result}

Using the inventory data and warehouse rules:
1. Prefer the warehouse geographically closest to the shipping destination.
2. Allocate from that warehouse if it has sufficient effective_allocatable stock.
3. If insufficient, split across warehouses (is_split=True, status=split_fulfillment).
4. If total stock across all warehouses is insufficient, status=backordered.

Set order_id to: {order_id}
Return a complete AllocationResult.
"""
        result = self._invoke_structured(
            prompt=prompt, 
            output_schema=AllocationResult,
            session_id=state.get("session_id", "default_session")
        )
        result.order_id = order_id

        if result.status == AllocationStatus.FAILED:
            new_status = FulfillmentStatus.ALLOCATION_FAILED
        elif result.status == AllocationStatus.BACKORDERED:
            new_status = FulfillmentStatus.ALLOCATION_FAILED
        elif result.status == AllocationStatus.SPLIT_FULFILLMENT:
            new_status = FulfillmentStatus.SPLIT_FULFILLMENT
        else:
            new_status = FulfillmentStatus.ALLOCATING_INVENTORY

        print(
            "InventoryAgent: order=%s allocation_status=%s warehouses=%s",
            order_id, result.status.value, result.warehouses_used,
        )
        return {"allocation_result": result, "status": new_status}
