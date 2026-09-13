
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.documents import DocumentLoader
from src.rag.vector_store import RagVectorStore

logging.basicConfig(level=logging.INFO)


def main():
    print("Building RAG FAISS Index...")
    loader = DocumentLoader()
    chunks = loader.load_all()
    
    if not chunks:
        print("Error: No markdown documents found in data/rag/")
        sys.exit(1)
        
    print(f"Loaded {len(chunks)} document chunks.")
    
    store = RagVectorStore()
    store.build_index(chunks)
    
    print("RAG index built successfully.")


if __name__ == "__main__":
    main()
