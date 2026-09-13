
from __future__ import annotations
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole, ReflectionResult, RoutingDecision
from src.models.fulfillment import FulfillmentStatus



class ReflectionAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.REFLECTION, **kwargs)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        order = state.get("order") or {}
        order_id = order.get("order_id", "unknown")
        print("ReflectionAgent: reviewing order %s" % (order_id))

        context = self.context_manager.prepare_agent_context(
            self.role, state.get("context") or {}
        )
        context_str = self.context_manager.context_to_prompt(context)

        prompt = f"""
You are the Reflection Agent. Review the entire fulfillment pipeline for quality.

{context_str}

Review checklist:
1. Was the order valid? Did validation_result show is_valid=True?
2. Was inventory allocated successfully? Check allocation_result.status.
3. Was a carrier selected? Check carrier_result.selected_carrier_id is not null.
4. For hazmat orders, was a hazmat-certified carrier used? (is_hazmat_compliant=True)
5. Was dispatch successful? Check dispatch_result.is_dispatched=True.
6. Does the shipping cost seem reasonable? (> 5x total order value would be anomalous)

If everything looks good:
- Set severity to "none"
- Set recommendation to "complete"
- Set confidence_score close to 1.0

If minor issues exist (non-blocking):
- Set severity to "low"
- Set recommendation to "complete"
- List issues in issues_found

If blocking issues exist that require reprocessing:
- Set severity to "high" or "critical"
- Set recommendation to the stage that should re-run (e.g., "select_carrier")
- List corrective_actions

Set order_id to: {order_id}
"""
        result = self._invoke_structured(
            prompt=prompt, 
            output_schema=ReflectionResult,
            session_id=state.get("session_id", "default_session")
        )
        result.order_id = order_id

        new_status = (
            FulfillmentStatus.COMPLETED
            if not result.needs_reprocessing
            else FulfillmentStatus.REFLECTING
        )

        print(
            "ReflectionAgent: order=%s severity=%s needs_reprocessing=%s confidence=%.2f",
            order_id, result.severity, result.needs_reprocessing, result.confidence_score,
        )
        return {"reflection_result": result, "status": new_status}
