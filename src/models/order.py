
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ShippingAddress(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State code (2-letter)")
    zip: str = Field(..., description="ZIP code")
    country: str = Field(default="US", description="Country code")


class OrderItem(BaseModel):
    sku: str = Field(..., description="Stock keeping unit identifier")
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: float = Field(..., ge=0, description="Price per unit")
    weight_kg: float = Field(..., ge=0, description="Weight per unit in kg")

    @property
    def total_weight(self) -> float:
        return self.quantity * self.weight_kg

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price


class OrderPriority(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    OVERNIGHT = "overnight"


class Order(BaseModel):
    order_id: str = Field(..., description="Unique order identifier")
    customer_id: str = Field(..., description="Customer identifier")
    customer_name: str = Field(..., description="Customer display name")
    order_date: datetime = Field(..., description="When the order was placed")
    priority: OrderPriority = Field(default=OrderPriority.STANDARD)
    shipping_address: ShippingAddress
    items: List[OrderItem] = Field(..., min_length=1)
    total_value: float = Field(..., ge=0, description="Total order value")
    required_delivery_date: datetime
    special_instructions: str = Field(default="", description="UNTRUSTED free-text — quarantined")
    is_hazmat: bool = Field(default=False)
    insurance_required: bool = Field(default=False)

    @property
    def total_weight(self) -> float:
        return sum(item.total_weight for item in self.items)

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.items)

    @property
    def item_skus(self) -> List[str]:
        return [item.sku for item in self.items]


class ValidationErrorDetail(BaseModel):
    code: str = Field(..., description="Error code (e.g., VAL-001)")
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Human-readable error message")


class OrderValidationResult(BaseModel):
    order_id: str
    is_valid: bool
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_notes: str = Field(default="", description="Agent reasoning notes")

    @property
    def error_codes(self) -> List[str]:
        return [e.code for e in self.errors]
