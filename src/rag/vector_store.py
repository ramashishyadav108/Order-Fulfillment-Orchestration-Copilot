
from __future__ import annotations
import pickle
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from src.config import settings
from src.rag.documents import DocumentChunk



class RagVectorStore:

    def __init__(self, index_path: Optional[Path] = None, embedding_model: Optional[str] = None):
        self._index_path = index_path or settings.FAISS_INDEX_PATH
        self._index_path.mkdir(parents=True, exist_ok=True)
        self._embedding_model_name = embedding_model or settings.EMBEDDING_MODEL
        self._index = None
        self._chunks: List[DocumentChunk] = []
        self._load_index()

    @property
    def model(self):
        from src.memory.semantic import _get_embedding_model
        return _get_embedding_model(self._embedding_model_name)

    def _load_index(self) -> None:
        index_file = self._index_path / "rag_docs.index"
        chunks_file = self._index_path / "rag_chunks.pkl"

        if index_file.exists() and chunks_file.exists():
            try:
                import faiss
                self._index = faiss.read_index(str(index_file))
                with open(chunks_file, "rb") as f:
                    self._chunks = pickle.load(f)
                print("Loaded RAG index: %d chunks" % (len(self._chunks)))
            except Exception as e:
                print("Failed to load RAG index: %s" % (e))
                self._index = None
                self._chunks = []

    def build_index(self, chunks: List[DocumentChunk]) -> None:
        if not chunks:
            print("No chunks provided to build_index")
            return

        import faiss

        # Extract texts for embedding
        texts = [chunk.content for chunk in chunks]
        
        print("Generating embeddings for %d chunks..." % (len(texts)))
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        
        # Initialize index
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity
        
        # Add to index
        self._index.add(embeddings.astype(np.float32))
        self._chunks = chunks
        
        # Save to disk
        index_file = self._index_path / "rag_docs.index"
        chunks_file = self._index_path / "rag_chunks.pkl"
        
        faiss.write_index(self._index, str(index_file))
        with open(chunks_file, "wb") as f:
            pickle.dump(self._chunks, f)
            
        print("RAG index built and saved successfully.")

    def search(self, query: str, top_k: int = 3, source_filter: Optional[str] = None) -> List[Tuple[DocumentChunk, float]]:
        if self._index is None or self._index.ntotal == 0:
            print("RAG index is empty or not loaded.")
            return []

        # Encode query
        query_embedding = self.model.encode([query], normalize_embeddings=True)

        # Search for more than top_k if filtering
        search_k = top_k * 3 if source_filter else top_k
        search_k = min(search_k, self._index.ntotal)
        
        scores, indices = self._index.search(query_embedding.astype(np.float32), search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._chunks):
                chunk = self._chunks[idx]
                if source_filter and chunk.source != source_filter:
                    continue
                    
                results.append((chunk, float(score)))
                
                if len(results) >= top_k:
                    break

        return results
