#!/usr/bin/env python3
"""Organize existing result files into structured folders"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import re


def organize_results(result_dir: str = "projects/example/result"):
    """Organize existing result files"""
    result_path = Path(result_dir)
    
    if not result_path.exists():
        print(f"Directory {result_dir} does not exist")
        return
    
    print(f"\n{'='*60}")
    print(f"Organizing results in: {result_dir}")
    print(f"{'='*60}\n")
    
    moved_count = 0
    
    # Process all JSON and PUML files
    for file in result_path.glob("*.*"):
        if file.is_file() and file.suffix in ['.json', '.puml']:
            # Skip if already in subdirectory
            if file.parent != result_path:
                continue
            
            # Extract date from filename (YYYYMMDD_HHMMSS)
            match = re.search(r'(\d{8})_\d{6}', file.name)
            if match:
                date_str = match.group(1)
            else:
                # Use file modification time
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                date_str = mtime.strftime("%Y%m%d")
            
            # Determine target directory
            if file.name.startswith('scenario_'):
                target_dir = result_path / "scenarios" / date_str
            elif file.name.startswith('loadtest_'):
                target_dir = result_path / "loadtests" / date_str
            elif file.suffix == '.puml':
                target_dir = result_path / "uml" / date_str
            else:
                # Unknown type, move to 'other'
                target_dir = result_path / "other" / date_str
            
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            target_file = target_dir / file.name
            
            # If file exists, add number suffix
            if target_file.exists():
                base = target_file.stem
                suffix = target_file.suffix
                counter = 1
                while target_file.exists():
                    target_file = target_dir / f"{base}_{counter}{suffix}"
                    counter += 1
            
            shutil.move(str(file), str(target_file))
            print(f"✓ Moved: {file.name}")
            print(f"  → {target_file.relative_to(result_path)}")
            moved_count += 1
    
    print(f"\n{'='*60}")
    print(f"✓ Organized {moved_count} files")
    print(f"{'='*60}\n")
    
    # Show directory structure
    print("New directory structure:")
    for root, dirs, files in os.walk(result_path):
        level = root.replace(str(result_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in sorted(files):
            if not file.startswith('.'):
                print(f"{subindent}{file}")


if __name__ == "__main__":
    organize_results()

