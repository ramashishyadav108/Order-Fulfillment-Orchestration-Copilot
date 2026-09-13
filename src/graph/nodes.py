
from __future__ import annotations
from typing import Any, Callable, Dict

from src.graph.state import FulfillmentState
from src.agents.supervisor import SupervisorAgent

from src.agents.validation import ValidationAgent
from src.agents.inventory import InventoryAgent
from src.agents.carrier import CarrierAgent
from src.agents.dispatch import DispatchAgent
from src.agents.reflection import ReflectionAgent
from src.models.fulfillment import FulfillmentStatus



def _merge_context(state: FulfillmentState, key: str, value: Any) -> Dict[str, Any]:
    ctx = dict(state.get("context") or {})
    if value is not None:
        ctx[key] = value.model_dump() if hasattr(value, "model_dump") else value
    return ctx





def create_supervisor_node(agent: SupervisorAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            res = agent.process(state)
            return res
        except Exception as e:
            print("Supervisor node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Supervisor error: {e}")
            res = {"errors": errors, "status": FulfillmentStatus.FAILED}
            return res
    return node


def create_validation_node(agent: ValidationAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            result = agent.process(state)
            vr = result.get("validation_result")
            ctx = _merge_context(state, "validation_result", vr)
            res = {
                "validation_result": vr,
                "status": result.get("status", state.get("status")),
                "context": ctx,
            }
            return res
        except Exception as e:
            print("Validation node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Validation error: {e}")
            res = {"errors": errors, "status": FulfillmentStatus.VALIDATION_FAILED}
            return res
    return node


def create_inventory_node(agent: InventoryAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            result = agent.process(state)
            ar = result.get("allocation_result")
            ctx = _merge_context(state, "allocation_result", ar)
            res = {
                "allocation_result": ar,
                "status": result.get("status", state.get("status")),
                "context": ctx,
            }
            return res
        except Exception as e:
            print("Inventory node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Inventory error: {e}")
            res = {"errors": errors, "status": FulfillmentStatus.ALLOCATION_FAILED}
            return res
    return node


def create_carrier_node(agent: CarrierAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            result = agent.process(state)
            cr = result.get("carrier_result")
            ctx = _merge_context(state, "carrier_result", cr)
            res = {
                "carrier_result": cr,
                "status": result.get("status", state.get("status")),
                "context": ctx,
            }
            return res
        except Exception as e:
            print("Carrier node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Carrier error: {e}")
            res = {"errors": errors, "status": FulfillmentStatus.CARRIER_SELECTION_FAILED}
            return res
    return node


def create_dispatch_node(agent: DispatchAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            result = agent.process(state)
            dr = result.get("dispatch_result")
            ctx = _merge_context(state, "dispatch_result", dr)
            res = {
                "dispatch_result": dr,
                "status": result.get("status", state.get("status")),
                "context": ctx,
            }
            return res
        except Exception as e:
            print("Dispatch node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Dispatch error: {e}")
            res = {"errors": errors, "status": FulfillmentStatus.FAILED}
            return res
    return node


def create_reflection_node(agent: ReflectionAgent) -> Callable:
    def node(state: FulfillmentState) -> Dict[str, Any]:
        try:
            result = agent.process(state)
            rr = result.get("reflection_result")
            res = {
                "reflection_result": rr,
                "status": result.get("status", state.get("status")),
            }
            return res
        except Exception as e:
            print("Reflection node error: %s" % (e,))
            errors = list(state.get("errors") or [])
            errors.append(f"Reflection error: {e}")
            # Don't fail the whole order on reflection error — mark complete
            res = {"errors": errors, "status": FulfillmentStatus.COMPLETED}
            return res
    return node
