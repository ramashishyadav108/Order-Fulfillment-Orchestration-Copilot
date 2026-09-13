
from __future__ import annotations
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import settings
from src.models.memory import MemoryEntry, MemoryTier, MemorySearchResult
from src.memory.short_term import ShortTermMemory
from src.memory.long_term import LongTermMemory
from src.memory.semantic import SemanticMemory
from src.memory.eviction import EvictionManager



class MemoryManager:

    def __init__(
        self,
        db_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        session_id: Optional[str] = None,
    ):
        self.session_id = session_id or str(uuid.uuid4())
        
        # Initialize tiers
        self.short_term = ShortTermMemory(capacity=100)
        self.short_term.set_session(self.session_id)
        
        self.long_term = LongTermMemory(
            db_path=db_path or settings.MEMORY_DB_PATH
        )
        
        self.semantic = SemanticMemory(
            index_path=index_path or (settings.RUNTIME_DIR / "memory" / "semantic"),
            embedding_model=settings.EMBEDDING_MODEL,
        )
        
        self.eviction = EvictionManager(
            max_entries=settings.MEMORY_MAX_ENTRIES,
            min_importance_to_keep=settings.MEMORY_EVICTION_THRESHOLD,
        )

        print("Memory manager initialized - session: %s" % (self.session_id))

    def store(
        self,
        key: str,
        content: str,
        tier: MemoryTier = MemoryTier.SHORT_TERM,
        importance: float = 0.5,
        order_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: Optional[int] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            tier=tier,
            key=key,
            content=content,
            importance_score=importance,
            session_id=self.session_id,
            order_id=order_id,
            metadata=metadata or {},
            ttl_hours=ttl_hours or (
                1 if tier == MemoryTier.SHORT_TERM
                else settings.MEMORY_TTL_HOURS
            ),
        )

        # Store in appropriate tier(s)
        if tier == MemoryTier.SHORT_TERM:
            self.short_term.store(key, content, metadata)
        elif tier == MemoryTier.LONG_TERM:
            self.long_term.store(entry)
            self.short_term.store(key, content, metadata)
        elif tier == MemoryTier.SEMANTIC:
            self.long_term.store(entry)
            self.semantic.store(entry)
            self.short_term.store(key, content, metadata)

        # Check eviction
        self._maybe_evict()

        print("Stored memory [%s] key=%s (importance=%.2f)" % (tier.value, key, importance))
        return entry

    def recall(self, key: str) -> Optional[str]:
        # Check short-term first
        result = self.short_term.recall(key)
        if result is not None:
            return result

        # Check long-term
        entry = self.long_term.recall(key)
        if entry:
            # Promote to short-term for faster future access
            self.short_term.store(key, entry.content)
            return entry.content

        return None

    def search_semantic(self, query: str, top_k: int = 5) -> List[MemorySearchResult]:
        return self.semantic.search(query, top_k)

    def recall_order_history(self, order_id: str) -> List[MemoryEntry]:
        return self.long_term.recall_by_order(order_id)

    def recall_session_history(self, session_id: Optional[str] = None) -> List[MemoryEntry]:
        return self.long_term.recall_by_session(session_id or self.session_id)

    def recall_from_previous_session(self, keyword: str) -> List[MemoryEntry]:
        results = self.long_term.search(keyword)
        # Filter out current session
        return [r for r in results if r.session_id != self.session_id]

    def get_context_for_agent(self, order_id: str = "") -> Dict[str, Any]:
        context = {
            "working_memory": self.short_term.get_context_summary(),
            "session_id": self.session_id,
        }

        if order_id:
            order_memories = self.recall_order_history(order_id)
            if order_memories:
                context["order_history"] = [
                    {"key": m.key, "content": m.content[:200], "session": m.session_id}
                    for m in order_memories[:5]
                ]

        return context

    def _maybe_evict(self) -> None:
        total = self.long_term.count()
        if self.eviction.should_evict(total):
            all_entries = self.long_term.get_all(limit=total)
            to_evict = self.eviction.select_for_eviction(all_entries)
            for memory_id in to_evict:
                self.long_term.delete(memory_id)
            print("Evicted %d memories" % (len(to_evict)))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "short_term_size": self.short_term.size,
            "long_term_size": self.long_term.count(),
            "semantic_size": self.semantic.size,
            "session_id": self.session_id,
        }

    def clear_all(self) -> None:
        self.short_term.clear()
        self.long_term.clear()
        self.semantic.clear()
        print("All memory tiers cleared")
