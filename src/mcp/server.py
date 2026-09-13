
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional

from src.mcp.tools import inventory_lookup as _inventory_lookup
from src.mcp.tools import carrier_rates as _carrier_rates
from src.mcp.resources import get_fulfillment_sop, get_carrier_rules, get_warehouse_rules

# Create the MCP server using FastMCP to avoid the low-level Server import bugs
mcp = FastMCP("fulfillment-mcp-server")


@mcp.tool()
def inventory_lookup(skus: List[str], warehouse_id: Optional[str] = None) -> str:
    result = _inventory_lookup(
        skus=skus,
        warehouse_id=warehouse_id,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def carrier_rates(
    total_weight_kg: float,
    destination_state: str,
    service_level: str = "standard",
    is_hazmat: bool = False,
    order_value: float = 0.0
) -> str:
    result = _carrier_rates(
        total_weight_kg=total_weight_kg,
        destination_state=destination_state,
        service_level=service_level,
        is_hazmat=is_hazmat,
        order_value=order_value,
    )
    return json.dumps(result, indent=2)


@mcp.resource("fulfillment://sop")
def read_fulfillment_sop() -> str:
    return get_fulfillment_sop()


if __name__ == "__main__":
    # FastMCP automatically handles stdio running and asyncio
    mcp.run()

