"""
Mem0 self-hosted configuration for OptiPlex 7010.
Uses Ollama (local) + Qdrant (Docker) — fully offline, no API keys needed.

Usage:
    from mem0_config import memory

    # Store a memory
    memory.add("James tracks three distinct HRV measurements", user_id="james")

    # Search memories
    results = memory.search("HRV tracking", user_id="james")

    # Get all memories
    all_mems = memory.get_all(user_id="james")
"""

from mem0 import Memory

config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "qwen3:8b",
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,
        },
    },
}

memory = Memory.from_config(config)
