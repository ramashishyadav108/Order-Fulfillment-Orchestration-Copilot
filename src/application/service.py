
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.models.order import Order
from src.models.fulfillment import FulfillmentStatus
from src.models.memory import MemoryTier
from src.context.manager import ContextManager
from src.memory.manager import MemoryManager
from src.graph.builder import build_fulfillment_graph
from src.graph.checkpointer import get_checkpointer






class FulfillmentService:

    def __init__(self, session_id: Optional[str] = None):
        self.context_manager = ContextManager()
        self.memory_manager = MemoryManager(session_id=session_id)
        self.checkpointer = get_checkpointer()
        self.graph = build_fulfillment_graph(
            context_manager=self.context_manager,
            checkpointer=self.checkpointer,
        )

    def process_order(self, order_dict: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        print("Starting order processing for thread: %s" % (thread_id))
        start_time = time.time()

        order = Order(**order_dict)
        


        context = self.context_manager.prepare_order_context(order)
        memory_context = self.memory_manager.get_context_for_agent(order.order_id)
        context["memory_context"] = memory_context

        order_json = json.loads(order.model_dump_json())
        order_json["total_weight"] = order.total_weight
        order_json["total_items"] = order.total_items
        order_json["item_skus"] = order.item_skus

        initial_state: Dict[str, Any] = {
            "order": order_json,
            "status": FulfillmentStatus.PENDING,
            "errors": [],
            "retry_count": 0,
            "context": context,
            "session_id": self.memory_manager.session_id,
            "validation_result": None,
            "allocation_result": None,
            "carrier_result": None,
            "dispatch_result": None,
            "reflection_result": None,
            "supervisor_decision": None,
        }

        config = {"configurable": {"thread_id": thread_id}}

        final_state: Optional[Dict[str, Any]] = None
        step = 0
        for event in self.graph.stream(initial_state, config=config, stream_mode="values"):
            step += 1
            node_status = event.get("status", "?")
            print("  Step %d - status: %s" % (step, node_status))
            final_state = event
            
            # Simple JSONL trace logging
            try:
                from src.config import settings
                if settings.TRACE_DIR:
                    settings.TRACE_DIR.mkdir(parents=True, exist_ok=True)
                    trace_path = settings.TRACE_DIR / f"{self.memory_manager.session_id}.jsonl"
                    with open(trace_path, "a") as f:
                        f.write(json.dumps({"step": step, "status": str(node_status), "state": json.loads(json.dumps(event, default=str))}) + "\n")
            except Exception:
                pass

        elapsed = round(time.time() - start_time, 2)
        print("Order %s completed in %.2fs (%d steps)" % (order.order_id, elapsed, step))

        if final_state:
            self._store_results_in_memory(final_state, order.order_id, elapsed)

        return final_state or {}

    def _store_results_in_memory(
        self, state: Dict[str, Any], order_id: str, elapsed: float
    ) -> None:
        raw_status = state.get("status", "unknown")
        status_str = raw_status.value if hasattr(raw_status, "value") else str(raw_status)

        self.memory_manager.store(
            key=f"order_{order_id}_summary",
            content=f"Order {order_id} completed with status={status_str} in {elapsed}s.",
            tier=MemoryTier.LONG_TERM,
            importance=0.8,
            order_id=order_id,
        )

        cr = state.get("carrier_result")
        if cr:
            carrier_name = (
                cr.get("selected_carrier_name") if isinstance(cr, dict)
                else getattr(cr, "selected_carrier_name", None)
            )
            if carrier_name:
                reason = (
                    cr.get("selection_reason") if isinstance(cr, dict)
                    else getattr(cr, "selection_reason", "")
                )
                self.memory_manager.store(
                    key=f"order_{order_id}_carrier",
                    content=f"Order {order_id} used carrier '{carrier_name}'. Reason: {reason}",
                    tier=MemoryTier.SEMANTIC,
                    importance=0.9,
                    order_id=order_id,
                )
