
from __future__ import annotations
from typing import Any, Dict

from langgraph.graph import StateGraph, START, END

from src.graph.state import FulfillmentState
from src.graph.nodes import (
    create_supervisor_node,
    create_validation_node,
    create_inventory_node,
    create_carrier_node,
    create_dispatch_node,
    create_reflection_node,
)
from src.graph.routing import (
    supervisor_router,
    validation_router,
    inventory_router,
    carrier_router,
    dispatch_router,
    reflection_router,
)
from src.agents.supervisor import SupervisorAgent
from src.agents.validation import ValidationAgent
from src.agents.inventory import InventoryAgent
from src.agents.carrier import CarrierAgent
from src.agents.dispatch import DispatchAgent
from src.agents.reflection import ReflectionAgent
from src.context.manager import ContextManager



def build_fulfillment_graph(
    context_manager: ContextManager,
    checkpointer: Any = None,
):
    
    # Initialize agents
    supervisor_agent = SupervisorAgent(context_manager=context_manager)
    validation_agent = ValidationAgent(context_manager=context_manager)
    inventory_agent = InventoryAgent(context_manager=context_manager)
    carrier_agent = CarrierAgent(context_manager=context_manager)
    dispatch_agent = DispatchAgent(context_manager=context_manager)
    reflection_agent = ReflectionAgent(context_manager=context_manager)
    
    # Initialize graph
    builder = StateGraph(FulfillmentState)
    
    # Add nodes
    builder.add_node("supervisor", create_supervisor_node(supervisor_agent))
    builder.add_node("validation", create_validation_node(validation_agent))
    builder.add_node("inventory", create_inventory_node(inventory_agent))
    builder.add_node("carrier", create_carrier_node(carrier_agent))
    builder.add_node("dispatch", create_dispatch_node(dispatch_agent))
    builder.add_node("reflection", create_reflection_node(reflection_agent))
    
    # Add edges
    builder.add_edge(START, "supervisor")
    
    # Conditional edges from supervisor
    builder.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "validation": "validation",
            "inventory": "inventory",
            "carrier": "carrier",
            "dispatch": "dispatch",
            "reflection": "reflection",
            "COMPLETE": END
        }
    )
    
    # Worker edges back to supervisor (or reflection)
    builder.add_conditional_edges(
        "validation",
        validation_router,
        {"supervisor": "supervisor"}
    )
    
    builder.add_conditional_edges(
        "inventory",
        inventory_router,
        {"supervisor": "supervisor"}
    )
    
    builder.add_conditional_edges(
        "carrier",
        carrier_router,
        {"supervisor": "supervisor"}
    )
    
    builder.add_conditional_edges(
        "dispatch",
        dispatch_router,
        {"reflection": "reflection"}
    )
    
    builder.add_conditional_edges(
        "reflection",
        reflection_router,
        {
            "validation": "validation",
            "inventory": "inventory",
            "carrier": "carrier",
            "dispatch": "dispatch",
            "COMPLETE": END
        }
    )
    
    # Compile graph
    graph = builder.compile(checkpointer=checkpointer)
    print("Fulfillment graph compiled successfully")
    return graph
