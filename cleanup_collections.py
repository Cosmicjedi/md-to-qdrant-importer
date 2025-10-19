"""
Cleanup Script - Delete Unwanted Qdrant Collections
This script will delete collections with a specific prefix from your Qdrant database.

Usage:
  python cleanup_collections.py <prefix_to_delete>

Example:
  python cleanup_collections.py game
  
This will delete: game_npcs, game_rulebooks, game_adventurepaths
"""

import sys
from qdrant_client import QdrantClient
from config import Config, get_config


def delete_collections_with_prefix(prefix: str, config: Config, dry_run: bool = False):
    """
    Delete all collections with the given prefix
    
    Args:
        prefix: Collection prefix to delete (e.g., 'game')
        config: Application configuration
        dry_run: If True, only show what would be deleted without actually deleting
    """
    # Connect to Qdrant
    client = QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
        prefer_grpc=False
    )
    
    # Get all collections
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]
    
    # Find collections with the specified prefix
    to_delete = [
        name for name in collection_names 
        if name.startswith(f"{prefix}_")
    ]
    
    if not to_delete:
        print(f"✓ No collections found with prefix '{prefix}_'")
        return
    
    print(f"Found {len(to_delete)} collection(s) with prefix '{prefix}_':")
    for name in to_delete:
        collection_info = client.get_collection(name)
        print(f"  - {name} ({collection_info.points_count} points)")
    
    if dry_run:
        print("\n[DRY RUN] Would delete these collections (run without --dry-run to actually delete)")
        return
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will permanently delete these collections and all their data!")
    response = input("Type 'yes' to confirm deletion: ")
    
    if response.lower() != 'yes':
        print("Cancelled - no collections were deleted")
        return
    
    # Delete collections
    print("\nDeleting collections...")
    for name in to_delete:
        try:
            client.delete_collection(name)
            print(f"  ✓ Deleted: {name}")
        except Exception as e:
            print(f"  ✗ Error deleting {name}: {e}")
    
    print("\n✓ Cleanup complete!")


def list_all_collections(config: Config):
    """
    List all collections in Qdrant
    
    Args:
        config: Application configuration
    """
    # Connect to Qdrant
    client = QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
        prefer_grpc=False
    )
    
    # Get all collections
    collections = client.get_collections().collections
    
    if not collections:
        print("No collections found in Qdrant")
        return
    
    print(f"Found {len(collections)} collection(s):")
    for collection in collections:
        info = client.get_collection(collection.name)
        print(f"  - {collection.name}: {info.points_count} points")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python cleanup_collections.py <prefix|--list> [--dry-run]")
        print("\nExamples:")
        print("  python cleanup_collections.py --list              # List all collections")
        print("  python cleanup_collections.py game --dry-run      # Show what would be deleted")
        print("  python cleanup_collections.py game                # Delete game_* collections")
        sys.exit(1)
    
    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Make sure your .env file is configured correctly")
        sys.exit(1)
    
    command = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    if command == '--list':
        list_all_collections(config)
    else:
        prefix = command
        delete_collections_with_prefix(prefix, config, dry_run=dry_run)


if __name__ == "__main__":
    main()
