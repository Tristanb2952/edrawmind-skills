#!/usr/bin/env python3
"""
build.py — Package the edrawmind-mindmap skill into a distributable zip.

Creates a zip archive containing the skill directory ready for end-user
installation. The ``docs/`` subdirectory is excluded (internal dev references).

Usage:
    python scripts/build.py                      # default: dist/edrawmind-mindmap.zip
    python scripts/build.py -o dist/custom.zip   # custom output path
    python scripts/build.py --list                # dry-run: list files only

Output structure (inside zip)::

    edrawmind-mindmap/
    ├── SKILL.md
    ├── license.txt
    ├── references/
    │   ├── markdown-format.md
    │   ├── style-guide.md
    │   └── tool-reference.md
    └── scripts/
        └── edrawmind_cli.py
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SKILL_DIR = _PROJECT_ROOT / "skills" / "edrawmind-mindmap"
_DEFAULT_OUTPUT = _PROJECT_ROOT / "dist" / "edrawmind-mindmap.zip"

# Directories to exclude from the zip (relative to _SKILL_DIR)
_EXCLUDE_DIRS = {"docs", "__pycache__"}


def _collect_files(skill_dir: Path) -> list[Path]:
    """Collect all files under *skill_dir*, excluding internal directories."""
    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if any(part in _EXCLUDE_DIRS for part in rel.parts):
            continue
        files.append(path)
    return files


def build(output: Path, *, dry_run: bool = False) -> int:
    """Build the skill zip. Returns 0 on success, 1 on error."""
    if not _SKILL_DIR.is_dir():
        print(f"Error: skill directory not found: {_SKILL_DIR}", file=sys.stderr)
        return 1

    files = _collect_files(_SKILL_DIR)
    if not files:
        print("Error: no files found to package.", file=sys.stderr)
        return 1

    archive_prefix = "edrawmind-mindmap"

    if dry_run:
        print(f"Files to include ({len(files)}):\n")
        for f in files:
            print(f"  {archive_prefix}/{f.relative_to(_SKILL_DIR)}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            arcname = f"{archive_prefix}/{f.relative_to(_SKILL_DIR)}"
            zf.write(f, arcname)

    size_kb = output.stat().st_size / 1024
    print(f"Built {output} ({size_kb:.1f} KB, {len(files)} files)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package the edrawmind-mindmap skill into a zip archive.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=f"Output zip path (default: {_DEFAULT_OUTPUT.relative_to(_PROJECT_ROOT)})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="dry_run",
        help="List files that would be included without creating the zip.",
    )
    args = parser.parse_args(argv)
    return build(args.output, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
