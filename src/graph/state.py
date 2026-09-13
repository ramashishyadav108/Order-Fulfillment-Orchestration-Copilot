
from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict
from datetime import datetime

from src.models.order import Order, OrderValidationResult
from src.models.inventory import AllocationResult
from src.models.carrier import CarrierSelectionResult
from src.models.fulfillment import DispatchResult, FulfillmentStatus
from src.models.agent import SupervisorDecision, ReflectionResult


class FulfillmentState(TypedDict):
    # Core data
    order: Optional[Dict[str, Any]]
    
    # Process results (populated progressively)
    validation_result: Optional[OrderValidationResult]
    allocation_result: Optional[AllocationResult]
    carrier_result: Optional[CarrierSelectionResult]
    dispatch_result: Optional[DispatchResult]
    reflection_result: Optional[ReflectionResult]
    supervisor_decision: Optional[SupervisorDecision]
    
    # Tracking
    status: FulfillmentStatus
    errors: List[str]
    retry_count: int
    
    # Context and Memory
    context: Dict[str, Any]
    session_id: str
