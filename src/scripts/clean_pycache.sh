#!/bin/bash
# Delete every __pycache__ directory under the repo (or a provided path).

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
TARGET_ROOT="${1:-$DEFAULT_ROOT}"

if [ ! -d "$TARGET_ROOT" ]; then
    echo "Error: $TARGET_ROOT is not a directory" >&2
    exit 1
fi

echo "🔍 Searching for __pycache__ directories under: $TARGET_ROOT"

found_any=0
while IFS= read -r -d '' dir; do
    found_any=1
    rm -rf -- "$dir"
    echo "🧹 Removed: $dir"
done < <(find "$TARGET_ROOT" -type d -name '__pycache__' -print0)

if [ "$found_any" -eq 0 ]; then
    echo "No __pycache__ directories found."
else
    echo "✅ Cleanup complete."
fi
