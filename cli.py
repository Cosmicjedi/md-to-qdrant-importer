#!/usr/bin/env python
"""
Command-line interface for MD to Qdrant Importer
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json

from config import get_config
from import_processor import ImportProcessor


def main():
    parser = argparse.ArgumentParser(
        description='Import markdown files to Qdrant vector database with NPC extraction'
    )
    
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to markdown file or directory containing markdown files'
    )
    
    parser.add_argument(
        '--env-file',
        type=str,
        default='.env',
        help='Path to environment file (default: .env)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Recursively process subdirectories (default: True)'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip files that already exist in database'
    )
    
    parser.add_argument(
        '--no-npc-extraction',
        action='store_true',
        help='Disable NPC extraction'
    )
    
    parser.add_argument(
        '--output-log',
        type=str,
        help='Path to save import results log'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration without processing'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config(args.env_file)
    
    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    if args.validate_only:
        print("Configuration is valid!")
        print(config)
        return 0
    
    # Set up progress callback
    def progress_callback(message, current=0, total=0):
        if args.verbose:
            if total > 0:
                print(f"[{current}/{total}] {message}")
            else:
                print(f"{message}")
    
    # Create processor
    processor = ImportProcessor(config, progress_callback)
    
    # Process input path
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        print(f"Error: Path '{input_path}' does not exist")
        return 1
    
    results = []
    
    try:
        if input_path.is_file():
            # Process single file
            if input_path.suffix.lower() not in ['.md', '.markdown']:
                print(f"Error: File '{input_path}' is not a markdown file")
                return 1
            
            print(f"Processing file: {input_path}")
            result = processor.process_file(
                input_path,
                skip_if_exists=args.skip_existing,
                extract_npcs=not args.no_npc_extraction
            )
            results = [result]
            
        else:
            # Process directory
            print(f"Processing directory: {input_path}")
            results = processor.process_directory(
                input_path,
                recursive=args.recursive,
                skip_existing=args.skip_existing,
                extract_npcs=not args.no_npc_extraction
            )
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        return 1
    
    except Exception as e:
        print(f"Error during processing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    
    total_files = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total_files - successful
    total_chunks = sum(r.chunks_imported for r in results)
    total_npcs = sum(r.npcs_extracted for r in results)
    
    print(f"Total files processed: {total_files}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"Total chunks imported: {total_chunks}")
    print(f"Total NPCs extracted: {total_npcs}")
    
    # Print failures if any
    if failed > 0:
        print("\nFailed files:")
        for r in results:
            if not r.success:
                print(f"  - {r.file_path}: {r.error}")
    
    # Save results log if requested
    if args.output_log:
        log_path = Path(args.output_log)
    else:
        # Auto-generate log filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = config.output_directory / f"import_log_{timestamp}.json"
    
    processor.save_results(results, log_path)
    print(f"\nResults saved to: {log_path}")
    
    # Get and display statistics
    stats = processor.get_stats()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    for collection_name, collection_stats in stats.items():
        if isinstance(collection_stats, dict) and 'points_count' in collection_stats:
            print(f"\n{collection_name}:")
            print(f"  Points: {collection_stats['points_count']}")
            print(f"  Vectors: {collection_stats['vectors_count']}")
            print(f"  Status: {collection_stats['status']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
