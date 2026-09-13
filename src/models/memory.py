
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class MemoryTier(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"


class EvictionPolicy(str, Enum):
    TTL = "ttl"
    LRU = "lru"
    IMPORTANCE_WEIGHTED = "importance_weighted"


class MemoryEntry(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier: MemoryTier
    key: str = Field(..., description="Lookup key for the memory")
    content: str = Field(..., description="The memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance_score: float = Field(
        default=0.5, ge=0, le=1,
        description="Importance weight: 1.0 = critical, 0.0 = trivial"
    )
    session_id: str = Field(default="", description="Session that created this memory")
    order_id: str = Field(default="", description="Related order ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0, ge=0)
    ttl_hours: Optional[int] = Field(default=None, description="Time-to-live in hours")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")

    def touch(self) -> None:
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    @property
    def is_expired(self) -> bool:
        if self.ttl_hours is None:
            return False
        elapsed = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        return elapsed > self.ttl_hours

    @property
    def eviction_score(self) -> float:
# Recency: hours since last access (lower = more recent = higher score)
        hours_since_access = (datetime.utcnow() - self.last_accessed).total_seconds() / 3600
        recency = max(0, 1 - (hours_since_access / 168))  # decay over 1 week

        # Frequency: normalize access count (log scale)
        import math
        frequency = min(1.0, math.log(1 + self.access_count) / math.log(100))

        return (self.importance_score * 0.5) + (recency * 0.3) + (frequency * 0.2)


class MemorySearchResult(BaseModel):
    entry: MemoryEntry
    similarity_score: float = Field(ge=0, le=1)
