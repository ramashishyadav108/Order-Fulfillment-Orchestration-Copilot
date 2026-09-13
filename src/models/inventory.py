
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    sku: str
    quantity_available: int = Field(ge=0)
    reserved: int = Field(ge=0)
    reorder_point: int = Field(ge=0)

    @property
    def effective_available(self) -> int:
        return max(0, self.quantity_available - self.reserved - self.reorder_point)

    @property
    def allocatable(self) -> int:
        return max(0, self.quantity_available - self.reserved - self.reorder_point)


class WarehouseLocation(BaseModel):
    city: str
    state: str
    zip: str


class Warehouse(BaseModel):
    warehouse_id: str
    name: str
    location: WarehouseLocation
    inventory: List[InventoryItem]

    def get_stock(self, sku: str) -> Optional[InventoryItem]:
        for item in self.inventory:
            if item.sku == sku:
                return item
        return None

    def get_allocatable(self, sku: str) -> int:
        stock = self.get_stock(sku)
        return stock.allocatable if stock else 0


class WarehouseInventory(BaseModel):
    warehouses: List[Warehouse]

    def find_warehouse(self, warehouse_id: str) -> Optional[Warehouse]:
        for wh in self.warehouses:
            if wh.warehouse_id == warehouse_id:
                return wh
        return None


class AllocationEntry(BaseModel):
    warehouse_id: str
    warehouse_name: str
    sku: str
    quantity_allocated: int = Field(ge=0)
    quantity_requested: int = Field(ge=0)
    is_partial: bool = False


class AllocationStatus(str, Enum):
    FULLY_ALLOCATED = "fully_allocated"
    PARTIALLY_ALLOCATED = "partially_allocated"
    SPLIT_FULFILLMENT = "split_fulfillment"
    BACKORDERED = "backordered"
    FAILED = "failed"


class AllocationResult(BaseModel):
    order_id: str
    status: AllocationStatus
    allocations: List[AllocationEntry] = Field(default_factory=list)
    is_split: bool = Field(default=False, description="True if fulfilled from multiple warehouses")
    warehouses_used: List[str] = Field(default_factory=list)
    unallocated_skus: List[str] = Field(default_factory=list)
    allocated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_notes: str = Field(default="")

    @property
    def total_allocated(self) -> int:
        return sum(a.quantity_allocated for a in self.allocations)
