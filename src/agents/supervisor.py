
from __future__ import annotations
from typing import Any, Dict

from src.agents.base import BaseAgent
from src.models.agent import AgentRole, SupervisorDecision, RoutingDecision
from src.models.fulfillment import FulfillmentStatus


# Deterministic state-machine mapping from status → next action
_STATUS_TO_ACTION: Dict[str, RoutingDecision] = {
    FulfillmentStatus.PENDING.value:               RoutingDecision.VALIDATE,
    FulfillmentStatus.VALIDATING.value:            RoutingDecision.ALLOCATE_INVENTORY,
    FulfillmentStatus.VALIDATION_FAILED.value:     RoutingDecision.HOLD,
    FulfillmentStatus.ALLOCATING_INVENTORY.value:  RoutingDecision.SELECT_CARRIER,
    FulfillmentStatus.SPLIT_FULFILLMENT.value:     RoutingDecision.SELECT_CARRIER,
    FulfillmentStatus.ALLOCATION_FAILED.value:     RoutingDecision.FAIL,
    FulfillmentStatus.SELECTING_CARRIER.value:     RoutingDecision.DISPATCH,
    FulfillmentStatus.CARRIER_SELECTION_FAILED.value: RoutingDecision.FAIL,
    FulfillmentStatus.DISPATCHING.value:           RoutingDecision.REFLECT,
    FulfillmentStatus.DISPATCHED.value:            RoutingDecision.REFLECT,
    FulfillmentStatus.REFLECTING.value:            RoutingDecision.COMPLETE,
    FulfillmentStatus.COMPLETED.value:             RoutingDecision.COMPLETE,
    FulfillmentStatus.ON_HOLD.value:               RoutingDecision.HOLD,
    FulfillmentStatus.FAILED.value:                RoutingDecision.FAIL,
    FulfillmentStatus.BACKORDERED.value:           RoutingDecision.FAIL,
}


class SupervisorAgent(BaseAgent):

    def __init__(self, **kwargs):
        super().__init__(role=AgentRole.SUPERVISOR, **kwargs)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Status may be a FulfillmentStatus enum OR a plain string (after serialisation)
        raw_status = state.get("status", FulfillmentStatus.PENDING)
        status_value = raw_status.value if hasattr(raw_status, "value") else str(raw_status)
        order_id = (state.get("order") or {}).get("order_id", "unknown")
        retry_count = state.get("retry_count", 0)

        print("Supervisor: order=%s  status=%s  retry=%d" % (order_id, status_value, retry_count))

        # Guard: too many retries → fail
        if retry_count >= 3:
            print("Supervisor: max retries reached for order %s - failing" % (order_id))
            action = RoutingDecision.FAIL
            reason = f"Max retries ({retry_count}) reached"
        else:
            action = _STATUS_TO_ACTION.get(status_value, RoutingDecision.VALIDATE)
            reason = f"Status '{status_value}' maps to action '{action.value}'"

        print("Supervisor decision: %s - %s" % (action.value, reason))

        decision = SupervisorDecision(
            order_id=order_id,
            next_action=action,
            reason=reason,
            retry_count=retry_count,
        )

        return {"supervisor_decision": decision}
