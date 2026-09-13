
from __future__ import annotations
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole
from src.models.order import OrderValidationResult
from src.models.fulfillment import FulfillmentStatus



class ValidationAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.VALIDATION, **kwargs)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        order = state.get("order") or {}
        order_id = order.get("order_id", "unknown")
        print("ValidationAgent processing order %s" % (order_id))

        context = self.context_manager.prepare_agent_context(
            self.role, state.get("context") or {}
        )
        context_str = self.context_manager.context_to_prompt(context)

        prompt = f"""
Validate this fulfillment order against all business rules.

{context_str}

Rules to check:
- customer_id must be non-empty
- shipping_address must have street, city, state, zip (all non-empty)
- all item quantities must be ≥ 1
- all item unit_prices must be > 0
- required_delivery_date must be after order_date
- if any SKU contains 'HAZ', is_hazmat must be True
- total_value must match sum of (quantity × unit_price) within $0.01 tolerance

Set order_id to: {order_id}
Set is_valid to True only if ALL checks pass.
"""
        result = self._invoke_structured(
            prompt=prompt, 
            output_schema=OrderValidationResult,
            session_id=state.get("session_id", "default_session")
        )
        result.order_id = order_id

        new_status = (
            FulfillmentStatus.VALIDATING
            if result.is_valid
            else FulfillmentStatus.VALIDATION_FAILED
        )
        print(
            "ValidationAgent: order=%s valid=%s errors=%d",
            order_id, result.is_valid, len(result.errors),
        )
        return {"validation_result": result, "status": new_status}
