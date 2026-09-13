
from __future__ import annotations

from src.graph.state import FulfillmentState
from src.models.agent import RoutingDecision
from src.models.fulfillment import FulfillmentStatus



def _status_str(state: FulfillmentState) -> str:
    raw = state.get("status", FulfillmentStatus.PENDING)
    return raw.value if hasattr(raw, "value") else str(raw)


def supervisor_router(state: FulfillmentState) -> str:
    decision = state.get("supervisor_decision")

    if not decision:
        print("No supervisor decision found - defaulting to COMPLETE")
        return "COMPLETE"

    # decision may be a Pydantic object or a dict (after LangGraph serialisation)
    if isinstance(decision, dict):
        action_val = decision.get("next_action", RoutingDecision.COMPLETE.value)
        action = RoutingDecision(action_val) if isinstance(action_val, str) else action_val
    else:
        action = decision.next_action

    routing_map = {
        RoutingDecision.VALIDATE:             "validation",
        RoutingDecision.ALLOCATE_INVENTORY:   "inventory",
        RoutingDecision.SELECT_CARRIER:       "carrier",
        RoutingDecision.DISPATCH:             "dispatch",
        RoutingDecision.REFLECT:              "reflection",
        RoutingDecision.COMPLETE:             "COMPLETE",
        RoutingDecision.HOLD:                 "COMPLETE",
        RoutingDecision.FAIL:                 "COMPLETE",
    }

    dest = routing_map.get(action, "COMPLETE")
    val = action.value if hasattr(action, "value") else action
    print("supervisor_router: %s -> %s" % (val, dest))
    return dest


def validation_router(state: FulfillmentState) -> str:
    return "supervisor"


def inventory_router(state: FulfillmentState) -> str:
    return "supervisor"


def carrier_router(state: FulfillmentState) -> str:
    return "supervisor"


def dispatch_router(state: FulfillmentState) -> str:
    return "reflection"


def reflection_router(state: FulfillmentState) -> str:
    result = state.get("reflection_result")
    if not result:
        return "COMPLETE"

    # Handle both Pydantic object and dict (after serialisation)
    if isinstance(result, dict):
        rec_val = result.get("recommendation", RoutingDecision.COMPLETE.value)
        try:
            rec = RoutingDecision(rec_val)
        except ValueError:
            rec = RoutingDecision.COMPLETE
        needs_reprocessing = rec not in (RoutingDecision.COMPLETE, RoutingDecision.FAIL)
    else:
        rec = result.recommendation
        needs_reprocessing = result.needs_reprocessing

    if not needs_reprocessing:
        return "COMPLETE"

    routing_map = {
        RoutingDecision.VALIDATE:           "validation",
        RoutingDecision.ALLOCATE_INVENTORY: "inventory",
        RoutingDecision.SELECT_CARRIER:     "carrier",
        RoutingDecision.DISPATCH:           "dispatch",
    }
    dest = routing_map.get(rec, "COMPLETE")
    print("reflection_router: self-healing -> %s" % (dest))
    return dest
