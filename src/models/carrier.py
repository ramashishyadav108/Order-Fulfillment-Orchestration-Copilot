
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CarrierRate(BaseModel):
    base_rate: float = Field(ge=0)
    per_kg: float = Field(ge=0)
    estimated_days: int = Field(ge=1)


class Carrier(BaseModel):
    carrier_id: str
    name: str
    service_levels: List[str]
    hazmat_certified: bool = False
    max_weight_kg: float = Field(ge=0)
    coverage_states: List[str]
    rates: Dict[str, CarrierRate]
    insurance_rate_percent: float = Field(ge=0)
    reliability_score: float = Field(ge=0, le=1)

    def covers_state(self, state: str) -> bool:
        return "ALL" in self.coverage_states or state in self.coverage_states

    def supports_service_level(self, level: str) -> bool:
        return level in self.service_levels

    def calculate_shipping_cost(self, weight_kg: float, service_level: str) -> Optional[float]:
        if service_level not in self.rates:
            return None
        rate = self.rates[service_level]
        return rate.base_rate + (rate.per_kg * weight_kg)

    def calculate_insurance_cost(self, order_value: float) -> float:
        return order_value * (self.insurance_rate_percent / 100)


class CarrierSelectionResult(BaseModel):
    order_id: str
    selected_carrier_id: Optional[str] = None
    selected_carrier_name: Optional[str] = None
    service_level: Optional[str] = None
    shipping_cost: Optional[float] = None
    insurance_cost: Optional[float] = None
    total_cost: Optional[float] = None
    estimated_delivery_days: Optional[int] = None
    selection_reason: str = ""
    alternatives_considered: List[Dict] = Field(default_factory=list)
    is_hazmat_compliant: bool = True
    selected_at: datetime = Field(default_factory=datetime.utcnow)
    agent_notes: str = Field(default="")

    @property
    def has_carrier(self) -> bool:
        return self.selected_carrier_id is not None
