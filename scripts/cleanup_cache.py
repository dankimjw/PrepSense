#!/usr/bin/env python3
# # PrepSense - Smart Pantry Management System
# # Copyright (c) 2025 Daniel Kim. All rights reserved.
# #
# # This software is proprietary and confidential. Unauthorized copying
# # of this file, via any medium, is strictly prohibited.

"""PrepSense Cache Cleanup Script - Removes build artifacts and temporary files"""

import os
import shutil
import sys
from pathlib import Path


class CacheCleanup:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.deleted_count = 0
        self.total_size = 0

    def get_size(self, path: Path) -> int:
        """Get size of file or directory in bytes"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
            return total
        return 0

    def format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def clean_pycache(self) -> tuple[int, int]:
        """Remove all __pycache__ directories and .pyc files"""
        count = 0
        size = 0

        # Remove __pycache__ directories
        for pycache_dir in self.repo_root.rglob("__pycache__"):
            if pycache_dir.is_dir():
                try:
                    dir_size = self.get_size(pycache_dir)
                    shutil.rmtree(pycache_dir)
                    count += 1
                    size += dir_size
                    print(f"  ✓ Removed: {pycache_dir.relative_to(self.repo_root)}")
                except Exception as e:
                    print(f"  ✗ Could not remove {pycache_dir.relative_to(self.repo_root)}: {e}")

        # Remove .pyc and .pyo files
        for pattern in ["*.pyc", "*.pyo"]:
            for pyc_file in self.repo_root.rglob(pattern):
                if "__pycache__" not in str(pyc_file):  # Skip if already deleted with dir
                    try:
                        file_size = pyc_file.stat().st_size
                        pyc_file.unlink()
                        count += 1
                        size += file_size
                    except Exception as e:
                        print(f"  ✗ Could not remove {pyc_file.relative_to(self.repo_root)}: {e}")

        return count, size

    def clean_system_files(self) -> tuple[int, int]:
        """Remove .DS_Store files"""
        count = 0
        size = 0
        for ds_file in self.repo_root.rglob(".DS_Store"):
            try:
                file_size = ds_file.stat().st_size
                ds_file.unlink()
                count += 1
                size += file_size
                print(f"  ✓ Removed: {ds_file.relative_to(self.repo_root)}")
            except Exception as e:
                print(f"  ✗ Could not remove {ds_file.relative_to(self.repo_root)}: {e}")
        return count, size

    def clean_test_cache(self) -> tuple[int, int]:
        """Remove test cache directories"""
        count = 0
        size = 0

        # Remove .pytest_cache
        for cache_dir in self.repo_root.rglob(".pytest_cache"):
            if cache_dir.is_dir():
                try:
                    dir_size = self.get_size(cache_dir)
                    shutil.rmtree(cache_dir)
                    count += 1
                    size += dir_size
                    print(f"  ✓ Removed: {cache_dir.relative_to(self.repo_root)}")
                except Exception as e:
                    print(f"  ✗ Could not remove {cache_dir.relative_to(self.repo_root)}: {e}")

        # Remove .mypy_cache
        mypy_cache = self.repo_root / ".mypy_cache"
        if mypy_cache.exists() and mypy_cache.is_dir():
            try:
                dir_size = self.get_size(mypy_cache)
                shutil.rmtree(mypy_cache)
                count += 1
                size += dir_size
                print("  ✓ Removed: .mypy_cache")
            except Exception as e:
                print(f"  ✗ Could not remove .mypy_cache: {e}")

        # Remove coverage files
        for coverage_file in self.repo_root.rglob(".coverage*"):
            if coverage_file.is_file():
                try:
                    file_size = coverage_file.stat().st_size
                    coverage_file.unlink()
                    count += 1
                    size += file_size
                    print(f"  ✓ Removed: {coverage_file.relative_to(self.repo_root)}")
                except Exception as e:
                    print(f"  ✗ Could not remove {coverage_file.relative_to(self.repo_root)}: {e}")

        return count, size

    def clean_logs(self) -> tuple[int, int]:
        """Remove log files"""
        count = 0
        size = 0
        for log_file in self.repo_root.rglob("*.log"):
            try:
                file_size = log_file.stat().st_size
                log_file.unlink()
                count += 1
                size += file_size
                print(f"  ✓ Removed: {log_file.relative_to(self.repo_root)}")
            except Exception as e:
                print(f"  ✗ Could not remove {log_file.relative_to(self.repo_root)}: {e}")
        return count, size

    def clean_old_backups(self) -> tuple[int, int]:
        """Remove old backup directories"""
        count = 0
        size = 0

        # Specific known backup directories
        backup_dirs = [".claude_backup_agents_20250806_155151", ".git-rewrite"]

        for dir_name in backup_dirs:
            backup_dir = self.repo_root / dir_name
            if backup_dir.exists() and backup_dir.is_dir():
                try:
                    dir_size = self.get_size(backup_dir)
                    shutil.rmtree(backup_dir)
                    count += 1
                    size += dir_size
                    print(f"  ✓ Removed: {dir_name}")
                except Exception as e:
                    print(f"  ✗ Could not remove {dir_name}: {e}")

        return count, size

    def clean_all(self, dry_run: bool = False) -> None:
        """Run all cleanup operations"""
        print("PrepSense Cache Cleanup")
        print(f"Repository: {self.repo_root}")
        print("=" * 60)

        if dry_run:
            print("DRY RUN MODE - No files will be deleted")
            print("=" * 60)

        total_count = 0
        total_size = 0

        # Python cache
        print("\n📦 Python Cache Files:")
        count, size = self.clean_pycache() if not dry_run else (0, 0)
        print(f"  Summary: {count} items, {self.format_size(size)}")
        total_count += count
        total_size += size

        # System files
        print("\n🖥️  System Files:")
        count, size = self.clean_system_files() if not dry_run else (0, 0)
        print(f"  Summary: {count} items, {self.format_size(size)}")
        total_count += count
        total_size += size

        # Test cache
        print("\n🧪 Test Cache:")
        count, size = self.clean_test_cache() if not dry_run else (0, 0)
        print(f"  Summary: {count} items, {self.format_size(size)}")
        total_count += count
        total_size += size

        # Log files
        print("\n📝 Log Files:")
        count, size = self.clean_logs() if not dry_run else (0, 0)
        print(f"  Summary: {count} items, {self.format_size(size)}")
        total_count += count
        total_size += size

        # Old backups
        print("\n🗄️  Old Backups:")
        count, size = self.clean_old_backups() if not dry_run else (0, 0)
        print(f"  Summary: {count} items, {self.format_size(size)}")
        total_count += count
        total_size += size

        # Final summary
        print("\n" + "=" * 60)
        print("✨ Cleanup Complete!")
        print(f"   Total items removed: {total_count}")
        print(f"   Total space freed: {self.format_size(total_size)}")

        if dry_run:
            print("\n💡 To perform actual cleanup, run without --dry-run flag")


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dry_run = "--dry-run" in sys.argv

    cleaner = CacheCleanup(repo_root)
    cleaner.clean_all(dry_run=dry_run)
