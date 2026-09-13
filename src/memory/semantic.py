
from __future__ import annotations
import json
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from src.models.memory import MemoryEntry, MemorySearchResult, MemoryTier


# ── Module-level singleton for the embedding model
# SentenceTransformer loads ~90 MB of weights; re-loading per order
# exhausts Windows virtual memory (os error 1455).
_EMBEDDING_MODELS: dict = {}


def _get_embedding_model(model_name: str):
    if model_name not in _EMBEDDING_MODELS:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model: %s (one-time)", model_name)
        _EMBEDDING_MODELS[model_name] = SentenceTransformer(model_name)
    return _EMBEDDING_MODELS[model_name]


class SemanticMemory:

    def __init__(self, index_path: str | Path, embedding_model: str = "BAAI/bge-small-en-v1.5"):
        self._index_path = Path(index_path)
        self._index_path.mkdir(parents=True, exist_ok=True)
        self._embedding_model_name = embedding_model
        self._index = None
        self._entries: List[MemoryEntry] = []
        self._load_index()

    @property
    def model(self):
        return _get_embedding_model(self._embedding_model_name)

    def _load_index(self) -> None:
        index_file = self._index_path / "semantic_memory.index"
        entries_file = self._index_path / "semantic_entries.pkl"

        if index_file.exists() and entries_file.exists():
            try:
                import faiss
                self._index = faiss.read_index(str(index_file))
                with open(entries_file, "rb") as f:
                    self._entries = pickle.load(f)
                print("Loaded semantic memory: %d entries" % (len(self._entries)))
            except Exception as e:
                print("Failed to load semantic memory index: %s" % (e))
                self._index = None
                self._entries = []

    def _save_index(self) -> None:
        if self._index is not None:
            import faiss
            index_file = self._index_path / "semantic_memory.index"
            entries_file = self._index_path / "semantic_entries.pkl"

            faiss.write_index(self._index, str(index_file))
            with open(entries_file, "wb") as f:
                pickle.dump(self._entries, f)

    def store(self, entry: MemoryEntry) -> None:
        import faiss

        # Generate embedding
        embedding = self.model.encode([entry.content], normalize_embeddings=True)

        # Initialize index if needed
        if self._index is None:
            dim = embedding.shape[1]
            self._index = faiss.IndexFlatIP(dim)  # Inner product (cosine sim with normalized vectors)

        # Add to index
        self._index.add(embedding.astype(np.float32))
        self._entries.append(entry)

        # Persist
        self._save_index()
        print("Stored semantic memory: %s" % (entry.key))

    def search(self, query: str, top_k: int = 5) -> List[MemorySearchResult]:
        if self._index is None or self._index.ntotal == 0:
            return []

        # Encode query
        query_embedding = self.model.encode([query], normalize_embeddings=True)

        # Search
        scores, indices = self._index.search(query_embedding.astype(np.float32), min(top_k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._entries):
                results.append(MemorySearchResult(
                    entry=self._entries[idx],
                    similarity_score=float(score),
                ))

        return results

    def clear(self) -> None:
        self._index = None
        self._entries = []
        # Remove files
        for f in self._index_path.glob("semantic_*"):
            f.unlink()
        print("Semantic memory cleared")

    @property
    def size(self) -> int:
        return len(self._entries)
