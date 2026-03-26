"""
Migrate memories from Mem0 Cloud (free tier) to self-hosted OpenMemory.

Usage:
  1. Set your Mem0 cloud API key: export MEM0_CLOUD_API_KEY=your_key
  2. Run: python3 migrate-memories.py

This exports all memories from cloud, then imports them into your local instance.
"""

import os
import json
import requests

CLOUD_API_KEY = os.environ.get("MEM0_CLOUD_API_KEY", "")
LOCAL_API_URL = "http://localhost:8765"
USER_ID = "james"


def export_from_cloud():
    """Export all memories from Mem0 cloud."""
    print("Exporting memories from Mem0 Cloud...")

    try:
        from mem0 import MemoryClient
        client = MemoryClient(api_key=CLOUD_API_KEY)
        memories = client.get_all(user_id=USER_ID)
        print(f"  Found {len(memories)} memories in cloud.")
        return memories
    except ImportError:
        print("  mem0ai package not installed. Install with: pip install mem0ai")
        print("  Alternatively, export manually from the Mem0 dashboard.")
        return []


def import_to_local(memories):
    """Import memories into local OpenMemory instance."""
    print(f"Importing {len(memories)} memories to local instance...")

    success = 0
    failed = 0

    for mem in memories:
        text = mem.get("memory", mem.get("text", ""))
        if not text:
            continue

        try:
            resp = requests.post(
                f"{LOCAL_API_URL}/v1/memories/",
                json={
                    "messages": [{"role": "user", "content": text}],
                    "user_id": USER_ID,
                },
            )
            if resp.status_code in (200, 201):
                success += 1
            else:
                failed += 1
                print(f"  Failed: {text[:60]}... ({resp.status_code})")
        except Exception as e:
            failed += 1
            print(f"  Error: {e}")

    print(f"  Imported: {success}, Failed: {failed}")


def main():
    if not CLOUD_API_KEY:
        print("Set MEM0_CLOUD_API_KEY environment variable first.")
        print("You can find it at: https://app.mem0.ai/settings/api-keys")
        return

    # Export
    memories = export_from_cloud()

    if not memories:
        print("No memories to migrate.")
        return

    # Save backup
    backup_path = "memories_backup.json"
    with open(backup_path, "w") as f:
        json.dump(memories, f, indent=2)
    print(f"  Backup saved to {backup_path}")

    # Import
    import_to_local(memories)
    print("\nMigration complete!")


if __name__ == "__main__":
    main()
