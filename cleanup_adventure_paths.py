#!/usr/bin/env python3
"""
Cleanup Script for Misplaced Adventure Path Data

This script helps identify and optionally delete:
1. Adventure path content incorrectly placed in rulebooks collection
2. NPCs extracted from adventure paths (campaign-specific characters)

Usage:
    python cleanup_adventure_paths.py --dry-run    # See what would be deleted
    python cleanup_adventure_paths.py --execute     # Actually delete the data
"""

import argparse
from pathlib import Path
from typing import List, Dict, Set
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import Config


def is_adventure_path_file(file_path: str) -> bool:
    """Check if a file path indicates an adventure path"""
    filename_lower = Path(file_path).name.lower()
    return "adventure" in filename_lower


def find_misplaced_adventure_paths(config: Config) -> Dict[str, List[str]]:
    """
    Find adventure path content in the rulebooks collection
    
    Returns:
        Dictionary mapping file paths to lists of point IDs
    """
    client = QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
        prefer_grpc=False
    )
    
    rulebooks_collection = config.qdrant_collection_rulebooks
    
    print(f"\n🔍 Scanning {rulebooks_collection} collection for misplaced adventure paths...")
    print("=" * 80)
    
    # Scroll through all points in rulebooks collection
    offset = None
    misplaced_files = {}
    total_points_checked = 0
    
    while True:
        result, next_offset = client.scroll(
            collection_name=rulebooks_collection,
            limit=100,
            offset=offset,
            with_payload=True
        )
        
        if not result:
            break
        
        for point in result:
            total_points_checked += 1
            file_path = point.payload.get('file_path', '')
            
            if is_adventure_path_file(file_path):
                if file_path not in misplaced_files:
                    misplaced_files[file_path] = []
                misplaced_files[file_path].append(point.id)
        
        offset = next_offset
        if offset is None:
            break
    
    print(f"✓ Checked {total_points_checked} points in {rulebooks_collection}")
    return misplaced_files


def find_adventure_path_npcs(config: Config) -> Dict[str, List[str]]:
    """
    Find NPCs that were extracted from adventure paths
    
    Returns:
        Dictionary mapping source files to lists of NPC point IDs
    """
    client = QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
        prefer_grpc=False
    )
    
    npcs_collection = config.qdrant_collection_npcs
    
    print(f"\n🔍 Scanning {npcs_collection} collection for adventure-specific NPCs...")
    print("=" * 80)
    
    offset = None
    adventure_npcs = {}
    total_npcs_checked = 0
    
    while True:
        result, next_offset = client.scroll(
            collection_name=npcs_collection,
            limit=100,
            offset=offset,
            with_payload=True
        )
        
        if not result:
            break
        
        for point in result:
            total_npcs_checked += 1
            source_file = point.payload.get('source_file', '')
            
            if is_adventure_path_file(source_file):
                if source_file not in adventure_npcs:
                    adventure_npcs[source_file] = []
                adventure_npcs[source_file].append(point.id)
        
        offset = next_offset
        if offset is None:
            break
    
    print(f"✓ Checked {total_npcs_checked} NPCs in {npcs_collection}")
    return adventure_npcs


def delete_points(
    config: Config,
    collection: str,
    point_ids: List[str]
):
    """Delete specified points from a collection"""
    client = QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
        prefer_grpc=False
    )
    
    client.delete(
        collection_name=collection,
        points_selector=point_ids
    )


def main():
    parser = argparse.ArgumentParser(
        description="Clean up misplaced adventure path data from Qdrant"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help="Actually delete the misplaced data (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")
    
    # Load configuration
    config = Config()
    
    print("\n" + "=" * 80)
    print("ADVENTURE PATH DATA CLEANUP UTILITY")
    print("=" * 80)
    
    # Find misplaced adventure paths
    misplaced_files = find_misplaced_adventure_paths(config)
    
    # Find adventure path NPCs
    adventure_npcs = find_adventure_path_npcs(config)
    
    # Report findings
    print("\n" + "=" * 80)
    print("📊 FINDINGS")
    print("=" * 80)
    
    if misplaced_files:
        total_chunks = sum(len(points) for points in misplaced_files.values())
        print(f"\n❌ Found {len(misplaced_files)} misplaced adventure path files:")
        print(f"   Total chunks to delete: {total_chunks}")
        
        for file_path, point_ids in sorted(misplaced_files.items()):
            print(f"\n   📁 {Path(file_path).name}")
            print(f"      Path: {file_path}")
            print(f"      Chunks: {len(point_ids)}")
    else:
        print("\n✓ No misplaced adventure paths found in rulebooks collection")
    
    if adventure_npcs:
        total_npcs = sum(len(points) for points in adventure_npcs.values())
        print(f"\n❌ Found {len(adventure_npcs)} files with adventure-specific NPCs:")
        print(f"   Total NPCs to delete: {total_npcs}")
        
        for source_file, point_ids in sorted(adventure_npcs.items()):
            print(f"\n   👤 NPCs from: {Path(source_file).name}")
            print(f"      Source: {source_file}")
            print(f"      Count: {len(point_ids)}")
    else:
        print("\n✓ No adventure-specific NPCs found in NPCs collection")
    
    # Execute or confirm dry run
    print("\n" + "=" * 80)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data was deleted")
        print("\nTo actually delete this data, run:")
        print("  python cleanup_adventure_paths.py --execute")
    
    elif args.execute:
        if not misplaced_files and not adventure_npcs:
            print("✓ Nothing to delete!")
            return
        
        print("⚠️  EXECUTING DELETION")
        print("\nDeleting misplaced data...")
        
        # Delete misplaced adventure path chunks
        if misplaced_files:
            for file_path, point_ids in misplaced_files.items():
                print(f"  Deleting {len(point_ids)} chunks from {Path(file_path).name}...")
                delete_points(
                    config,
                    config.qdrant_collection_rulebooks,
                    point_ids
                )
        
        # Delete adventure-specific NPCs
        if adventure_npcs:
            for source_file, point_ids in adventure_npcs.items():
                print(f"  Deleting {len(point_ids)} NPCs from {Path(source_file).name}...")
                delete_points(
                    config,
                    config.qdrant_collection_npcs,
                    point_ids
                )
        
        print("\n✓ Cleanup complete!")
        print("\nNext steps:")
        print("1. Re-import your adventure path files with the fixed code")
        print("2. Verify data in Qdrant dashboard: http://localhost:6333/dashboard")
    
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
