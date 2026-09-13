
from __future__ import annotations
import json
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole
from src.models.carrier import CarrierSelectionResult
from src.models.fulfillment import FulfillmentStatus
from src.mcp.client import get_mcp_tools
from src.rag.rag_tool import get_rag_tools



class CarrierAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.CARRIER, **kwargs)
        mcp_tools = get_mcp_tools()
        rag_tools = get_rag_tools()
        self.carrier_tool = next((t for t in mcp_tools if t.name == "carrier_rates"), None)
        self.rag_rules_tool = next(
            (t for t in rag_tools if t.name == "lookup_carrier_rules"), None
        )

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        order = state.get("order") or {}
        order_id = order.get("order_id", "unknown")
        is_hazmat = order.get("is_hazmat", False)
        priority = order.get("priority", "standard")
        total_weight = order.get("total_weight", 0)
        total_value = order.get("total_value", 0)
        dest_state = (order.get("shipping_address") or {}).get("state", "")

        print(
            "CarrierAgent: order=%s hazmat=%s priority=%s weight=%.1fkg",
            order_id, is_hazmat, priority, total_weight,
        )

# ── Step 1: MCP carrier_rates tool
        carrier_data = "{}"
        if self.carrier_tool:
            try:
                tool_input = {
                    "total_weight_kg": total_weight,
                    "destination_state": dest_state,
                    "service_level": priority,
                    "is_hazmat": is_hazmat,
                    "order_value": total_value,
                }
                carrier_data = self.carrier_tool.invoke(tool_input)
                print("CarrierAgent: MCP carrier_rates returned %d chars" % (len(carrier_data)))
            except Exception as e:
                print("CarrierAgent: MCP tool error: %s" % (e))
                carrier_data = json.dumps({"error": str(e)})

# ── Step 2: RAG carrier rules lookup
        rag_context = ""
        if self.rag_rules_tool:
            try:
                query = f"carrier selection rules for {'hazmat' if is_hazmat else 'standard'} {priority} shipment"
                rag_context = self.rag_rules_tool.invoke(query)
                print("CarrierAgent: RAG rules retrieved (%d chars)", len(rag_context))
            except Exception as e:
                print("CarrierAgent: RAG lookup failed: %s" % (e))

# ── Step 3: Context + LLM decision
        context = self.context_manager.prepare_agent_context(
            self.role, state.get("context") or {}
        )
        context_str = self.context_manager.context_to_prompt(context)

        prompt = f"""
You are the Carrier Selection Agent.

{context_str}

Carrier Rates (from MCP carrier_rates tool):
{carrier_data}

Carrier Rules (from RAG lookup):
{rag_context if rag_context else 'No additional rules retrieved.'}

Select the BEST eligible carrier from the eligible_carriers list:
- If is_hazmat=True, only hazmat_certified carriers are valid (rule CR-001).
- Match the required service level (CR-004).
- For express/overnight, reliability_score must be ≥ 0.90 (CR-007).
- Minimize total_cost (CR-005).
- Record your reasoning in selection_reason.

Set order_id to: {order_id}
If no eligible carrier exists, set selected_carrier_id to null.
"""
        result = self._invoke_structured(
            prompt=prompt, 
            output_schema=CarrierSelectionResult,
            session_id=state.get("session_id", "default_session")
        )
        result.order_id = order_id

        new_status = (
            FulfillmentStatus.SELECTING_CARRIER
            if result.has_carrier
            else FulfillmentStatus.CARRIER_SELECTION_FAILED
        )
        print(
            "CarrierAgent: order=%s carrier=%s cost=%.2f",
            order_id,
            result.selected_carrier_name or "NONE",
            result.total_cost or 0,
        )
        return {"carrier_result": result, "status": new_status}
