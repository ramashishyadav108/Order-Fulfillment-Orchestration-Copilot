
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import OrderedDict



class ShortTermMemory:

    def __init__(self, capacity: int = 100):
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._capacity = capacity
        self._session_id: str = ""
        self._created_at = datetime.utcnow()

    def set_session(self, session_id: str) -> None:
        self._session_id = session_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        if key in self._store:
            # Move to end (most recent)
            self._store.move_to_end(key)

        self._store[key] = {
            "value": value,
            "metadata": metadata or {},
            "stored_at": datetime.utcnow().isoformat(),
            "session_id": self._session_id,
            "access_count": 0,
        }

        # Evict oldest if over capacity
        while len(self._store) > self._capacity:
            evicted_key, _ = self._store.popitem(last=False)
            print("Short-term memory evicted: %s" % (evicted_key))

    def recall(self, key: str) -> Optional[Any]:
        if key in self._store:
            self._store[key]["access_count"] += 1
            self._store.move_to_end(key)  # Mark as recently accessed
            return self._store[key]["value"]
        return None

    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        items = list(self._store.items())[-n:]
        return [{"key": k, **v} for k, v in items]

    def get_all(self) -> Dict[str, Any]:
        return dict(self._store)

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        results = []
        for key, entry in self._store.items():
            value_str = str(entry["value"]).lower()
            if keyword.lower() in key.lower() or keyword.lower() in value_str:
                results.append({"key": key, **entry})
        return results

    def clear(self) -> None:
        self._store.clear()
        print("Short-term memory cleared")

    @property
    def size(self) -> int:
        return len(self._store)

    def get_context_summary(self) -> str:
        if not self._store:
            return "Working memory is empty."

        entries = self.get_recent(5)
        lines = ["Recent working memory:"]
        for entry in entries:
            val = str(entry["value"])[:100]
            lines.append(f"  - {entry['key']}: {val}")
        return "\n".join(lines)
