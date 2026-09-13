
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    VALIDATION = "validation"
    INVENTORY = "inventory"
    CARRIER = "carrier"
    DISPATCH = "dispatch"
    REFLECTION = "reflection"


class AgentResponse(BaseModel):
    agent_role: AgentRole
    success: bool
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tools_used: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="", description="Agent's reasoning trace")


class RoutingDecision(str, Enum):
    VALIDATE = "validate"
    ALLOCATE_INVENTORY = "allocate_inventory"
    SELECT_CARRIER = "select_carrier"
    DISPATCH = "dispatch"
    REFLECT = "reflect"
    HOLD = "hold"
    COMPLETE = "complete"
    FAIL = "fail"


class SupervisorDecision(BaseModel):
    order_id: str
    next_action: RoutingDecision
    reason: str = ""
    context_summary: str = ""
    retry_count: int = 0
    max_retries: int = 3
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReflectionResult(BaseModel):
    order_id: str
    issues_found: List[str] = Field(default_factory=list)
    severity: str = Field(default="none", description="none | low | medium | high | critical")
    recommendation: RoutingDecision = RoutingDecision.COMPLETE
    corrective_actions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1, default=1.0)
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def needs_reprocessing(self) -> bool:
        return self.recommendation not in (RoutingDecision.COMPLETE, RoutingDecision.FAIL)
