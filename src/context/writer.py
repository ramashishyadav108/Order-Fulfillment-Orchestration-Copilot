
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
from src.models.order import Order


class ContextWriter:

    @staticmethod
    def write_order_context(order: Order) -> Dict[str, Any]:
        return {
            "metadata": {
                "context_type": "order",
                "order_id": order.order_id,
                "created_at": datetime.utcnow().isoformat(),
                "source": "order_intake",
                "trust_level": "trusted",
            },
            "order_summary": {
                "order_id": order.order_id,
                "customer_id": order.customer_id,
                "customer_name": order.customer_name,
                "priority": order.priority.value,
                "total_value": order.total_value,
                "total_weight_kg": order.total_weight,
                "total_items": order.total_items,
                "is_hazmat": order.is_hazmat,
                "insurance_required": order.insurance_required,
                "order_date": order.order_date.isoformat(),
                "required_delivery_date": order.required_delivery_date.isoformat(),
            },
            "shipping": {
                "street": order.shipping_address.street,
                "city": order.shipping_address.city,
                "state": order.shipping_address.state,
                "zip": order.shipping_address.zip,
                "country": order.shipping_address.country,
            },
            "items": [
                {
                    "sku": item.sku,
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "weight_kg": item.weight_kg,
                    "line_total": item.line_total,
                    "total_weight": item.total_weight,
                }
                for item in order.items
            ],
        }

    @staticmethod
    def write_agent_handoff_context(
        from_agent: str,
        to_agent: str,
        result: Dict[str, Any],
        summary: str,
    ) -> Dict[str, Any]:
        return {
            "metadata": {
                "context_type": "agent_handoff",
                "from_agent": from_agent,
                "to_agent": to_agent,
                "created_at": datetime.utcnow().isoformat(),
                "trust_level": "internal",
            },
            "summary": summary,
            "result": result,
        }

    @staticmethod
    def write_tool_result_context(
        tool_name: str,
        result: Any,
        success: bool,
    ) -> Dict[str, Any]:
        return {
            "metadata": {
                "context_type": "tool_result",
                "tool_name": tool_name,
                "created_at": datetime.utcnow().isoformat(),
                "trust_level": "tool_output",
                "success": success,
            },
            "result": result if isinstance(result, (dict, list, str)) else str(result),
        }
