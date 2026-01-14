#!/usr/bin/env python3
"""
Script to convert all UUID(as_uuid=True) columns to String(36) in SQLAlchemy models.

This fixes the PostgreSQL type mismatch error:
"operator does not exist: character varying = uuid"

Handles both:
- Legacy: Column(UUID(as_uuid=True), ...)
- SQLAlchemy 2.0: mapped_column(UUID(as_uuid=True), ...)

Run: python3 scripts/fix_uuid_columns.py
"""

import os
import re
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "app" / "models"

def fix_file(filepath: Path) -> tuple[int, list[str]]:
    """Fix UUID columns in a single file. Returns (changes_count, changes_list)."""

    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    changes = []

    # ==================== Legacy Column() patterns ====================

    # Pattern 1: id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern1 = r'(\s+)(\w+)\s*=\s*Column\(\s*UUID\(as_uuid=True\)\s*,\s*primary_key=True\s*,\s*default=uuid\.uuid4\)'
    replacement1 = r'\1\2 = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))'
    count1 = len(re.findall(pattern1, content))
    if count1:
        content = re.sub(pattern1, replacement1, content)
        changes.append(f"  - {count1} Column primary keys: UUID -> String(36)")

    # Pattern 2: Column(UUID(as_uuid=True), ForeignKey(...), ...)
    pattern2 = r'Column\(\s*UUID\(as_uuid=True\)\s*,\s*ForeignKey'
    replacement2 = 'Column(String(36), ForeignKey'
    count2 = len(re.findall(pattern2, content))
    if count2:
        content = re.sub(pattern2, replacement2, content)
        changes.append(f"  - {count2} Column ForeignKeys: UUID -> String(36)")

    # Pattern 3: Column(UUID(as_uuid=True), nullable=...)
    pattern3 = r'Column\(\s*UUID\(as_uuid=True\)\s*,\s*nullable'
    replacement3 = 'Column(String(36), nullable'
    count3 = len(re.findall(pattern3, content))
    if count3:
        content = re.sub(pattern3, replacement3, content)
        changes.append(f"  - {count3} Column nullable: UUID -> String(36)")

    # Pattern 4: Any remaining Column(UUID(as_uuid=True)...)
    pattern4 = r'Column\(UUID\(as_uuid=True\)'
    replacement4 = 'Column(String(36)'
    count4 = len(re.findall(pattern4, content))
    if count4:
        content = re.sub(pattern4, replacement4, content)
        changes.append(f"  - {count4} Column remaining: UUID -> String(36)")

    # ==================== SQLAlchemy 2.0 mapped_column() patterns ====================

    # Pattern 5: mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Multi-line version
    pattern5 = r'mapped_column\(\s*\n\s*UUID\(as_uuid=True\)\s*,\s*\n\s*primary_key=True\s*,\s*\n\s*default=uuid\.uuid4'
    replacement5 = 'mapped_column(\n        String(36),\n        primary_key=True,\n        default=lambda: str(uuid.uuid4())'
    count5 = len(re.findall(pattern5, content))
    if count5:
        content = re.sub(pattern5, replacement5, content)
        changes.append(f"  - {count5} mapped_column primary keys: UUID -> String(36)")

    # Pattern 6: mapped_column(UUID(as_uuid=True), ForeignKey(...), ...) multi-line
    pattern6 = r'mapped_column\(\s*\n\s*UUID\(as_uuid=True\)\s*,\s*\n\s*ForeignKey'
    replacement6 = 'mapped_column(\n        String(36),\n        ForeignKey'
    count6 = len(re.findall(pattern6, content))
    if count6:
        content = re.sub(pattern6, replacement6, content)
        changes.append(f"  - {count6} mapped_column ForeignKeys: UUID -> String(36)")

    # Pattern 7: mapped_column(UUID(as_uuid=True), nullable=...) multi-line
    pattern7 = r'mapped_column\(\s*\n\s*UUID\(as_uuid=True\)\s*,\s*\n\s*nullable'
    replacement7 = 'mapped_column(\n        String(36),\n        nullable'
    count7 = len(re.findall(pattern7, content))
    if count7:
        content = re.sub(pattern7, replacement7, content)
        changes.append(f"  - {count7} mapped_column nullable: UUID -> String(36)")

    # Pattern 8: Single-line mapped_column(UUID(as_uuid=True), ...)
    pattern8 = r'mapped_column\(UUID\(as_uuid=True\)'
    replacement8 = 'mapped_column(String(36)'
    count8 = len(re.findall(pattern8, content))
    if count8:
        content = re.sub(pattern8, replacement8, content)
        changes.append(f"  - {count8} mapped_column single-line: UUID -> String(36)")

    # ==================== Type hints ====================

    # Pattern 9: Mapped[uuid.UUID] -> Mapped[str]
    pattern9 = r'Mapped\[uuid\.UUID\]'
    replacement9 = 'Mapped[str]'
    count9 = len(re.findall(pattern9, content))
    if count9:
        content = re.sub(pattern9, replacement9, content)
        changes.append(f"  - {count9} type hints: Mapped[uuid.UUID] -> Mapped[str]")

    # Pattern 10: Mapped[Optional[uuid.UUID]] -> Mapped[Optional[str]]
    pattern10 = r'Mapped\[Optional\[uuid\.UUID\]\]'
    replacement10 = 'Mapped[Optional[str]]'
    count10 = len(re.findall(pattern10, content))
    if count10:
        content = re.sub(pattern10, replacement10, content)
        changes.append(f"  - {count10} type hints: Mapped[Optional[uuid.UUID]] -> Mapped[Optional[str]]")

    # ==================== Cleanup ====================

    # Remove unused UUID import if no UUID usage remains
    if 'UUID(as_uuid=True)' not in content and 'UUID(' not in content:
        if 'from sqlalchemy.dialects.postgresql import UUID' in content:
            content = content.replace('from sqlalchemy.dialects.postgresql import UUID\n', '')
            changes.append("  - Removed unused UUID import")

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return len(changes), changes

    return 0, []


def main():
    print("=" * 60)
    print("Fixing UUID columns in SQLAlchemy models")
    print("=" * 60)
    print()

    total_files = 0
    total_changes = 0

    for filepath in sorted(MODELS_DIR.glob("*.py")):
        if filepath.name == "__init__.py" or filepath.name == "base.py":
            continue

        count, changes = fix_file(filepath)

        if count > 0:
            total_files += 1
            total_changes += count
            print(f"✓ {filepath.name}:")
            for change in changes:
                print(change)
            print()

    print("=" * 60)
    print(f"Summary: Fixed {total_changes} patterns in {total_files} files")
    print("=" * 60)
    print()

    # Check for remaining UUID usages
    remaining = 0
    for filepath in MODELS_DIR.glob("*.py"):
        with open(filepath) as f:
            if 'UUID(as_uuid=True)' in f.read():
                remaining += 1
                print(f"⚠ Still has UUID: {filepath.name}")

    if remaining:
        print(f"\n⚠ {remaining} files still have UUID patterns that need manual review")
    else:
        print("✓ All files converted successfully!")


if __name__ == "__main__":
    main()
