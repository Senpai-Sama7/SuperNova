"""Test retrieval quality benchmarks."""

import pytest
from unittest.mock import AsyncMock
from supernova.core.memory.retrieval import WeightedMemoryRetriever, MemoryItem


@pytest.fixture
def mock_store():
    """Mock memory store for testing."""
    store = AsyncMock()
    return store


@pytest.fixture
def retriever(mock_store):
    """Create retriever with mock store."""
    stores = {"test": (mock_store, 0.8)}
    return WeightedMemoryRetriever(stores)


@pytest.mark.asyncio
async def test_relevant_memories_score_higher(retriever, mock_store):
    """Test that relevant memories score higher than irrelevant ones."""
    relevant = MemoryItem("1", "Python programming tutorial", "semantic", 0.9, 0.5, 0.0)
    irrelevant = MemoryItem("2", "Cooking recipes", "semantic", 0.2, 0.5, 0.0)
    
    mock_store.search.return_value = [relevant, irrelevant]
    
    results = await retriever.retrieve("Python coding help")
    
    assert results[0].id == "1"
    assert results[0].composite_score > results[1].composite_score


@pytest.mark.asyncio 
async def test_recently_accessed_memories_boosted(retriever, mock_store):
    """Test that recently accessed memories get access frequency boost."""
    old_memory = MemoryItem("1", "Old content", "semantic", 0.7, 0.3, 0.0)
    new_memory = MemoryItem("2", "New content", "semantic", 0.7, 0.3, 0.0)
    
    # Simulate previous access to new_memory
    retriever._access_counts["2"] = 5
    retriever._access_counts["1"] = 1
    
    mock_store.search.return_value = [old_memory, new_memory]
    
    results = await retriever.retrieve("test query")
    
    assert results[0].id == "2"  # More accessed memory should rank higher


@pytest.mark.asyncio
async def test_high_salience_memories_rank_higher(retriever, mock_store):
    """Test that high-salience memories rank above low-salience."""
    high_salience = MemoryItem("1", "Critical error occurred", "episodic", 0.6, 0.5, 0.0, salience_score=0.8)
    low_salience = MemoryItem("2", "Regular log entry", "episodic", 0.6, 0.5, 0.0, salience_score=0.1)
    
    mock_store.search.return_value = [low_salience, high_salience]
    
    results = await retriever.retrieve("system events")
    
    # High salience should boost ranking despite same base scores
    assert results[0].id == "1"


@pytest.mark.asyncio
async def test_access_frequency_affects_ranking(retriever, mock_store):
    """Test that access frequency affects final ranking."""
    memory_a = MemoryItem("a", "Content A", "semantic", 0.5, 0.5, 0.0)
    memory_b = MemoryItem("b", "Content B", "semantic", 0.5, 0.5, 0.0)
    
    # Set different access frequencies
    retriever._access_counts["a"] = 10
    retriever._access_counts["b"] = 2
    
    mock_store.search.return_value = [memory_a, memory_b]
    
    results = await retriever.retrieve("test")
    
    # Memory A should rank higher due to access frequency
    assert results[0].id == "a"
    assert retriever.get_access_frequency("a") == 10
    assert retriever.get_access_frequency("b") == 2