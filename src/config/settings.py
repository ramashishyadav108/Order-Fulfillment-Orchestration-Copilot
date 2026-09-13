
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ── Suppress non-critical SDK warnings globally
# AFC recommendation: not an error, just a stylistic suggestion from google-genai
warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")
warnings.filterwarnings("ignore", message=".*AFC is enabled.*")

# ── Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = PROJECT_ROOT / "runtime"

# ── LLM Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# ── Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# ── Memory Configuration
MEMORY_DB_PATH = RUNTIME_DIR / os.getenv("MEMORY_DB_PATH", "memory/memory.db")
CHECKPOINT_DB_PATH = RUNTIME_DIR / os.getenv("CHECKPOINT_DB_PATH", "checkpoints/checkpoints.db")
MEMORY_MAX_ENTRIES = int(os.getenv("MEMORY_MAX_ENTRIES", "1000"))
MEMORY_TTL_HOURS = int(os.getenv("MEMORY_TTL_HOURS", "168"))
MEMORY_EVICTION_THRESHOLD = float(os.getenv("MEMORY_EVICTION_THRESHOLD", "0.3"))

# ── RAG Configuration
FAISS_INDEX_PATH = RUNTIME_DIR / os.getenv("FAISS_INDEX_PATH", "rag/faiss_index")
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "512"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
RAG_DOCS_DIR = DATA_DIR / "rag"

# ── Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = RUNTIME_DIR / os.getenv("LOG_DIR", "logs")
TRACE_DIR = PROJECT_ROOT / os.getenv("TRACE_DIR", "evidence/traces")

# ── Data Paths
ORDERS_DIR = DATA_DIR / "orders"
INVENTORY_FILE = DATA_DIR / "inventory" / "synthetic_inventory.json"
CARRIERS_FILE = DATA_DIR / "carriers" / "synthetic_carrier_rates.json"

# ── MCP Server Configuration
MCP_SERVER_SCRIPT = PROJECT_ROOT / "src" / "mcp" / "server.py"


def ensure_directories():
    for dir_path in [
        RUNTIME_DIR,
        RUNTIME_DIR / "checkpoints",
        RUNTIME_DIR / "memory",
        RUNTIME_DIR / "logs",
        RUNTIME_DIR / "rag",
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)


def validate_config():
    errors = []
    if not GOOGLE_API_KEY:
        errors.append("GOOGLE_API_KEY environment variable is not set")
    if errors:
        raise ValueError(
            "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )


# Ensure runtime directories exist on import
ensure_directories()
