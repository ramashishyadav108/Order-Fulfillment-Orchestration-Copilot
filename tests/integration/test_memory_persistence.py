"""
Integration tests for memory persistence.
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.memory.manager import MemoryManager
from src.models.memory import MemoryTier


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield Path(path)
    try:
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass  # Windows file locking issue with sqlite


@pytest.fixture
def temp_index_path():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.mark.memory
def test_cross_session_persistence(temp_db_path, temp_index_path):
    """Test that long-term memory persists across manager instances (AC-07)."""
    
    # Session 1
    mem1 = MemoryManager(
        db_path=temp_db_path,
        index_path=temp_index_path,
        session_id="session-1"
    )
    
    mem1.store(
        key="test_fact_1",
        content="This is a persistent fact",
        tier=MemoryTier.LONG_TERM
    )
    
    # Verify it's in mem1
    assert mem1.recall("test_fact_1") == "This is a persistent fact"
    
    # Clean up mem1
    del mem1
    
    # Session 2 (new instance, same DB)
    mem2 = MemoryManager(
        db_path=temp_db_path,
        index_path=temp_index_path,
        session_id="session-2"
    )
    
    # Recall fact from session 1
    recalled = mem2.recall("test_fact_1")
    
    # Assert persistence
    assert recalled == "This is a persistent fact"
    
    # Check that recall_from_previous_session works
    prev_memories = mem2.recall_from_previous_session("test_fact_1")
    assert len(prev_memories) > 0
    assert prev_memories[0].session_id == "session-1"
