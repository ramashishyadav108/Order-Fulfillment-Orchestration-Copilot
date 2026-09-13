
from __future__ import annotations
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from src.config import settings



def get_checkpointer(db_path: Path | None = None) -> SqliteSaver:
    path = db_path or settings.CHECKPOINT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # We need an open connection for SqliteSaver
        # In a real app we'd manage this context properly
        import sqlite3
        conn = sqlite3.connect(str(path), check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        print("Initialized SQLite checkpointer at %s" % (path))
        return checkpointer
    except Exception as e:
        print("Failed to initialize checkpointer: %s" % (e))
        raise
