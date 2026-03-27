"""Quick test to verify Mem0 + Ollama + Qdrant are working."""

from mem0_config import memory

print("=== Mem0 Self-Hosted Test ===\n")

# Test 1: Store a memory
print("[1] Storing a test memory...")
result = memory.add("This is a test memory from the self-hosted setup.", user_id="james")
print(f"    Stored: {result}\n")

# Test 2: Search for it
print("[2] Searching for 'test memory'...")
results = memory.search("test memory", user_id="james")
for r in results:
    print(f"    Found: {r}\n")

# Test 3: List all memories
print("[3] Listing all memories...")
all_mems = memory.get_all(user_id="james")
print(f"    Total memories: {len(all_mems)}")
for m in all_mems:
    print(f"    - {m}\n")

print("=== Test Complete ===")
