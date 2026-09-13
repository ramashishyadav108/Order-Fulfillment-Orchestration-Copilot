
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import uuid


class FulfillmentStatus(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    ALLOCATING_INVENTORY = "allocating_inventory"
    ALLOCATION_FAILED = "allocation_failed"
    SELECTING_CARRIER = "selecting_carrier"
    CARRIER_SELECTION_FAILED = "carrier_selection_failed"
    DISPATCHING = "dispatching"
    DISPATCHED = "dispatched"
    SPLIT_FULFILLMENT = "split_fulfillment"
    BACKORDERED = "backordered"
    ON_HOLD = "on_hold"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


class ShipmentInfo(BaseModel):
    shipment_id: str = Field(default_factory=lambda: f"SHP-{uuid.uuid4().hex[:8].upper()}")
    tracking_number: str = Field(default_factory=lambda: f"TRK-{uuid.uuid4().hex[:12].upper()}")
    carrier_id: str
    carrier_name: str
    service_level: str
    warehouse_id: str
    items_shipped: List[Dict] = Field(default_factory=list)
    estimated_delivery: Optional[datetime] = None
    shipping_cost: float = 0.0


class DispatchResult(BaseModel):
    order_id: str
    dispatch_id: str = Field(default_factory=lambda: f"DSP-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}")
    is_dispatched: bool = False
    shipments: List[ShipmentInfo] = Field(default_factory=list)
    total_shipping_cost: float = 0.0
    total_insurance_cost: float = 0.0
    dispatched_at: Optional[datetime] = None
    notes: str = ""
    agent_notes: str = Field(default="")

    @property
    def shipment_count(self) -> int:
        return len(self.shipments)


class FulfillmentResult(BaseModel):
    order_id: str
    status: FulfillmentStatus
    validation_passed: bool = False
    allocation_success: bool = False
    carrier_selected: bool = False
    dispatch_success: bool = False
    is_split_order: bool = False
    total_cost: float = 0.0
    error_summary: List[str] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    completed_at: Optional[datetime] = None
