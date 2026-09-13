
from __future__ import annotations
from datetime import datetime
from typing import List, Tuple

from src.models.memory import MemoryEntry



class EvictionManager:

    def __init__(
        self,
        max_entries: int = 1000,
        eviction_batch_size: int = 50,
        min_importance_to_keep: float = 0.3,
    ):
        self.max_entries = max_entries
        self.eviction_batch_size = eviction_batch_size
        self.min_importance_to_keep = min_importance_to_keep

    def should_evict(self, current_count: int) -> bool:
        return current_count >= self.max_entries

    def select_for_eviction(self, entries: List[MemoryEntry]) -> List[str]:
        to_evict = []

        # Phase 1: Evict all expired entries (TTL-based)
        for entry in entries:
            if entry.is_expired:
                to_evict.append(entry.memory_id)
                print("TTL eviction: %s (key=%s)", entry.memory_id, entry.key)

        # Phase 2: If still over capacity, evict by lowest eviction_score
        remaining = [e for e in entries if e.memory_id not in set(to_evict)]
        entries_after_ttl = len(entries) - len(to_evict)

        if entries_after_ttl > self.max_entries:
# Sort by eviction_score (ascending = lowest priority first)
            scored = sorted(remaining, key=lambda e: e.eviction_score)

            # Evict entries with score below threshold first
            num_to_evict = min(
                self.eviction_batch_size,
                entries_after_ttl - self.max_entries + self.eviction_batch_size,
            )

            for entry in scored[:num_to_evict]:
                if entry.eviction_score < self.min_importance_to_keep:
                    to_evict.append(entry.memory_id)
                    print(
                        "Score eviction: %s (key=%s, score=%.3f)",
                        entry.memory_id, entry.key, entry.eviction_score,
                    )

            # If still not enough, evict lowest-scored regardless
            if len(entries) - len(to_evict) > self.max_entries:
                for entry in scored:
                    if entry.memory_id not in set(to_evict):
                        to_evict.append(entry.memory_id)
                        if len(entries) - len(to_evict) <= self.max_entries:
                            break

        print(
            "Eviction selected %d entries for removal (from %d total)",
            len(to_evict), len(entries),
        )
        return to_evict

    def get_eviction_report(self, entries: List[MemoryEntry]) -> dict:
        expired = sum(1 for e in entries if e.is_expired)
        scores = [e.eviction_score for e in entries]

        return {
            "total_entries": len(entries),
            "max_entries": self.max_entries,
            "expired_count": expired,
            "below_threshold": sum(1 for s in scores if s < self.min_importance_to_keep),
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "needs_eviction": len(entries) >= self.max_entries,
        }
