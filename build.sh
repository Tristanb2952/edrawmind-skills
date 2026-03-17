#!/usr/bin/env bash
# Build script for Linux/Mac — packages edrawmind-mindmap skill into a zip.
# Usage: ./build.sh [options]
#   ./build.sh              Build dist/edrawmind-mindmap.zip
#   ./build.sh --list       List files only (dry run)
#   ./build.sh -o out.zip   Custom output path

cd "$(dirname "$0")"
python3 scripts/build.py "$@"
