
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole
from src.models.fulfillment import DispatchResult, FulfillmentStatus



class DispatchAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.DISPATCH, **kwargs)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        order = state.get("order") or {}
        order_id = order.get("order_id", "unknown")
        print("DispatchAgent: finalising order %s" % (order_id))

        context = self.context_manager.prepare_agent_context(
            self.role, state.get("context") or {}
        )
        context_str = self.context_manager.context_to_prompt(context)

        prompt = f"""
You are the Dispatch Agent. Create the final dispatch record for this order.

{context_str}

Instructions:
- Generate a dispatch_id in format DSP-YYYY-XXXXXX (use today's year and a random hex suffix).
- Create one ShipmentInfo per warehouse used in the allocation (look at allocation_result.warehouses_used).
- For each shipment, set a realistic tracking_number like TRK-XXXXXXXXXXXXXXXX.
- Set estimated_delivery based on carrier's estimated_days from today.
- Set is_dispatched to True.
- Calculate total_shipping_cost and total_insurance_cost from carrier_result.
- Add any relevant notes.

Set order_id to: {order_id}
"""
        result = self._invoke_structured(
            prompt=prompt, 
            output_schema=DispatchResult,
            session_id=state.get("session_id", "default_session")
        )
        result.order_id = order_id
        result.is_dispatched = True

        print(
            "DispatchAgent: order=%s dispatch_id=%s shipments=%d",
            order_id, result.dispatch_id, result.shipment_count,
        )
        return {"dispatch_result": result, "status": FulfillmentStatus.DISPATCHED}
