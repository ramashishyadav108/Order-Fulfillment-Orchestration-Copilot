
from __future__ import annotations
import json
from typing import Any, Dict, Optional
from src.models.order import Order
from src.models.agent import AgentRole
from src.context.writer import ContextWriter
from src.context.selector import ContextSelector
from src.context.compressor import ContextCompressor
from src.context.quarantine import ContextQuarantine



class ContextManager:

    def __init__(self):
        self.writer = ContextWriter()
        self.selector = ContextSelector()
        self.compressor = ContextCompressor()
        self.quarantine = ContextQuarantine()

    def prepare_order_context(self, order: Order) -> Dict[str, Any]:
        # Step 1: WRITE — structure the order data
        context = self.writer.write_order_context(order)

        # Step 2: ISOLATE — quarantine untrusted free-text
        order_dict = order.model_dump(mode="json")
        sanitized_order, quarantine_envelope = self.quarantine.quarantine_order_text(order_dict)

        context["quarantine_envelope"] = quarantine_envelope
        context["quarantined_text_display"] = self.quarantine.format_for_agent(quarantine_envelope)

        print(
            "Context prepared for order %s - quarantine flags: %d"
            % (order.order_id, len(quarantine_envelope.get("injection_flags", [])))
        )

        return context

    def prepare_agent_context(
        self,
        agent_role: AgentRole,
        full_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Step 1: SELECT — filter to relevant fields
        selected = self.selector.select_for_agent(agent_role, full_context)

        # Step 2: COMPRESS — if context is too large
        compressed = self.compressor.compress(selected)

        return compressed

    def create_handoff_context(
        self,
        from_agent: str,
        to_agent: str,
        result: Dict[str, Any],
        summary: str,
    ) -> Dict[str, Any]:
        return self.writer.write_agent_handoff_context(
            from_agent, to_agent, result, summary
        )

    def add_tool_result(
        self,
        context: Dict[str, Any],
        tool_name: str,
        result: Any,
        success: bool,
    ) -> Dict[str, Any]:
        tool_context = self.writer.write_tool_result_context(tool_name, result, success)

        if "tool_results" not in context:
            context["tool_results"] = []
        context["tool_results"].append(tool_context)

        return context

    def get_system_prompt(self, agent_role: AgentRole) -> str:
        return self.selector.get_agent_system_prompt(agent_role)

    def context_to_prompt(self, context: Dict[str, Any]) -> str:
        parts = []

        if "order_summary" in context:
            parts.append("## Order Summary")
            for k, v in context["order_summary"].items():
                parts.append(f"- {k}: {v}")

        if "shipping" in context:
            parts.append("\n## Shipping Address")
            for k, v in context["shipping"].items():
                parts.append(f"- {k}: {v}")

        if "items" in context:
            parts.append("\n## Order Items")
            for item in context["items"]:
                parts.append(f"- {item['sku']}: {item['name']} × {item['quantity']} @ ${item['unit_price']}")

        if "validation_result" in context:
            parts.append("\n## Validation Result")
            parts.append(json.dumps(context["validation_result"], default=str, indent=2))

        if "allocation_result" in context:
            parts.append("\n## Allocation Result")
            parts.append(json.dumps(context["allocation_result"], default=str, indent=2))

        if "carrier_result" in context:
            parts.append("\n## Carrier Selection Result")
            parts.append(json.dumps(context["carrier_result"], default=str, indent=2))

        if "dispatch_result" in context:
            parts.append("\n## Dispatch Result")
            parts.append(json.dumps(context["dispatch_result"], default=str, indent=2))

        if "quarantined_text_display" in context:
            parts.append(f"\n## Customer Notes\n{context['quarantined_text_display']}")

        if "compressed_history" in context:
            parts.append(f"\n## Previous Processing History\n{context['compressed_history']}")

        if "memory_context" in context:
            parts.append("\n## Memory Context")
            parts.append(str(context["memory_context"]))

        if "errors" in context:
            parts.append("\n## Errors")
            for err in context["errors"]:
                parts.append(f"- ❌ {err}")

        return "\n".join(parts)
