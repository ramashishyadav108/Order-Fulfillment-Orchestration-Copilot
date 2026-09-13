"""
MCP Tool implementations for the fulfillment domain.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_inventory() -> Dict[str, Any]:
    """Load synthetic inventory data."""
    with open(DATA_DIR / "inventory" / "synthetic_inventory.json", "r") as f:
        return json.load(f)


def load_carriers() -> Dict[str, Any]:
    """Load synthetic carrier rates data."""
    with open(DATA_DIR / "carriers" / "synthetic_carrier_rates.json", "r") as f:
        return json.load(f)


def inventory_lookup(skus: List[str], warehouse_id: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP Tool 1: Look up inventory levels for given SKUs across warehouses.
    
    Args:
        skus: List of SKU identifiers to check
        warehouse_id: Optional specific warehouse to check (checks all if None)
    
    Returns:
        Stock levels per SKU per warehouse
    """
    data = load_inventory()
    results = {"skus_requested": skus, "warehouse_filter": warehouse_id, "stock": []}

    for warehouse in data["warehouses"]:
        if warehouse_id and warehouse["warehouse_id"] != warehouse_id:
            continue

        for inv_item in warehouse["inventory"]:
            if inv_item["sku"] in skus:
                available = inv_item["quantity_available"] - inv_item["reserved"]
                effective = max(0, available - inv_item["reorder_point"])
                results["stock"].append({
                    "warehouse_id": warehouse["warehouse_id"],
                    "warehouse_name": warehouse["name"],
                    "warehouse_location": warehouse["location"],
                    "sku": inv_item["sku"],
                    "quantity_available": inv_item["quantity_available"],
                    "reserved": inv_item["reserved"],
                    "net_available": available,
                    "effective_allocatable": effective,
                    "reorder_point": inv_item["reorder_point"],
                    "below_reorder": available <= inv_item["reorder_point"],
                })

    results["total_effective_by_sku"] = {}
    for stock in results["stock"]:
        sku = stock["sku"]
        if sku not in results["total_effective_by_sku"]:
            results["total_effective_by_sku"][sku] = 0
        results["total_effective_by_sku"][sku] += stock["effective_allocatable"]

    return results


def carrier_rates(
    total_weight_kg: float,
    destination_state: str,
    service_level: str = "standard",
    is_hazmat: bool = False,
    order_value: float = 0.0,
) -> Dict[str, Any]:
    """
    MCP Tool 2: Get carrier rates and eligibility for given shipment parameters.
    
    Args:
        total_weight_kg: Total weight of shipment in kg
        destination_state: Destination state code (2-letter)
        service_level: Required service level (standard/express/overnight)
        is_hazmat: Whether shipment contains hazmat items
        order_value: Order value for insurance calculation
    
    Returns:
        Eligible carriers with rates, sorted by cost
    """
    data = load_carriers()
    results = {
        "request": {
            "weight_kg": total_weight_kg,
            "destination": destination_state,
            "service_level": service_level,
            "is_hazmat": is_hazmat,
            "order_value": order_value,
        },
        "eligible_carriers": [],
        "ineligible_carriers": [],
    }

    for carrier in data["carriers"]:
        ineligible_reasons = []

        # Check hazmat certification
        if is_hazmat and not carrier["hazmat_certified"]:
            ineligible_reasons.append("Not hazmat certified")

        # Check weight limit
        if total_weight_kg > carrier["max_weight_kg"]:
            ineligible_reasons.append(f"Weight {total_weight_kg}kg exceeds max {carrier['max_weight_kg']}kg")

        # Check coverage
        if "ALL" not in carrier["coverage_states"] and destination_state not in carrier["coverage_states"]:
            ineligible_reasons.append(f"Does not cover state {destination_state}")

        # Check service level
        if service_level not in carrier["service_levels"]:
            ineligible_reasons.append(f"Does not offer {service_level} service")

        if ineligible_reasons:
            results["ineligible_carriers"].append({
                "carrier_id": carrier["carrier_id"],
                "carrier_name": carrier["name"],
                "reasons": ineligible_reasons,
            })
        else:
            rate = carrier["rates"][service_level]
            shipping_cost = rate["base_rate"] + (rate["per_kg"] * total_weight_kg)
            insurance_cost = order_value * (carrier["insurance_rate_percent"] / 100) if order_value > 0 else 0

            results["eligible_carriers"].append({
                "carrier_id": carrier["carrier_id"],
                "carrier_name": carrier["name"],
                "service_level": service_level,
                "shipping_cost": round(shipping_cost, 2),
                "insurance_cost": round(insurance_cost, 2),
                "total_cost": round(shipping_cost + insurance_cost, 2),
                "estimated_days": rate["estimated_days"],
                "reliability_score": carrier["reliability_score"],
                "hazmat_certified": carrier["hazmat_certified"],
                "max_weight_kg": carrier["max_weight_kg"],
            })

    # Sort eligible by total cost
    results["eligible_carriers"].sort(key=lambda c: c["total_cost"])

    return results
