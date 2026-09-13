
from __future__ import annotations
from typing import Any, Dict, List, Optional
from src.models.agent import AgentRole


# Define what context each agent role needs
AGENT_CONTEXT_MAP: Dict[AgentRole, List[str]] = {
    AgentRole.SUPERVISOR: [
        "order_summary", "shipping", "items", "validation_result",
        "allocation_result", "carrier_result", "dispatch_result",
        "reflection_result", "errors", "memory_context",
    ],
    AgentRole.VALIDATION: [
        "order_summary", "shipping", "items",
    ],
    AgentRole.INVENTORY: [
        "order_summary", "items", "shipping",
        "validation_result",
    ],
    AgentRole.CARRIER: [
        "order_summary", "shipping", "items",
        "allocation_result",
    ],
    AgentRole.DISPATCH: [
        "order_summary", "shipping", "items",
        "allocation_result", "carrier_result",
    ],
    AgentRole.REFLECTION: [
        "order_summary", "validation_result",
        "allocation_result", "carrier_result", "dispatch_result",
        "errors", "memory_context",
    ],
}


class ContextSelector:

    @staticmethod
    def select_for_agent(
        agent_role: AgentRole,
        full_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        allowed_keys = AGENT_CONTEXT_MAP.get(agent_role, [])
        selected = {}
        for key in allowed_keys:
            if key in full_context:
                selected[key] = full_context[key]
        
        # Always include metadata
        if "metadata" in full_context:
            selected["metadata"] = full_context["metadata"]
        
        return selected

    @staticmethod
    def get_agent_system_prompt(agent_role: AgentRole) -> str:
        prompts = {
            AgentRole.SUPERVISOR: (
                "You are the Fulfillment Supervisor Agent. Your role is to orchestrate "
                "the order fulfillment process by routing orders to specialized worker "
                "agents. Analyze the current state and decide the next action: validate, "
                "allocate_inventory, select_carrier, dispatch, reflect, hold, complete, or fail. "
                "Provide clear reasoning for your routing decisions."
            ),
            AgentRole.VALIDATION: (
                "You are the Order Validation Agent. Validate the order against business rules: "
                "check customer ID, shipping address completeness, item quantities (must be positive), "
                "SKU format, total value accuracy, delivery date feasibility, and hazmat flags. "
                "Return a structured validation result with any errors found."
            ),
            AgentRole.INVENTORY: (
                "You are the Inventory Allocation Agent. Allocate stock from warehouses to fulfill "
                "the order. Use the inventory_lookup tool to check stock levels. Apply warehouse "
                "proximity rules and handle stock-out by splitting across warehouses if needed. "
                "Never allocate below reorder points."
            ),
            AgentRole.CARRIER: (
                "You are the Carrier Selection Agent. Select the optimal carrier for the shipment. "
                "Use the carrier_rates tool to get rates. Apply carrier rules: hazmat certification, "
                "weight limits, regional coverage, service level matching. Optimize for cost while "
                "maintaining reliability. Use the carrier rules lookup for complex decisions."
            ),
            AgentRole.DISPATCH: (
                "You are the Dispatch Agent. Finalize the fulfillment by creating dispatch records. "
                "Generate dispatch IDs, assign tracking numbers, and confirm carrier assignments. "
                "Verify all pre-dispatch quality checks are met."
            ),
            AgentRole.REFLECTION: (
                "You are the Reflection Agent. Review the fulfillment decisions for quality and "
                "compliance. Check for cost anomalies, SLA violations, rule violations, and "
                "potential issues. If problems are found, recommend corrective action by routing "
                "back to the appropriate agent. Provide a confidence score for the overall fulfillment."
            ),
        }
        return prompts.get(agent_role, "You are a fulfillment agent.")
