#!/usr/bin/env bash
# datalad-checkpoint.sh — Stop hook: auto-checkpoint after each Claude turn
# Fires once per turn (not per file edit). Always exits 0; never blocks or warns.

set -euo pipefail

# Guard 1: datalad not available
if ! command -v datalad >/dev/null 2>&1; then
  exit 0
fi

# Guard 2: not inside a datalad dataset (search cwd and parents for .datalad/)
check_dir="$PWD"
found_dataset=0
while [[ "$check_dir" != "/" ]]; do
  if [[ -d "$check_dir/.datalad" ]]; then
    found_dataset=1
    break
  fi
  check_dir="$(dirname "$check_dir")"
done
if [[ $found_dataset -eq 0 ]]; then
  exit 0
fi

# Guard 3: explicit opt-out
if [[ "${DATALAD_AUTOSAVE:-}" == "0" ]]; then
  exit 0
fi

# Check for modified/untracked files (exclude annex objects)
status_output="$(datalad status --annex none 2>/dev/null || true)"
if [[ -z "$status_output" ]]; then
  exit 0
fi

# Build commit message
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# Extract file list from status output (second field of each line)
file_list="$(echo "$status_output" | awk '{print $NF}' | tr '\n' ' ' | sed 's/ $//')"

# Truncate file list if too long
if [[ ${#file_list} -gt 80 ]]; then
  file_list="${file_list:0:77}..."
fi

commit_msg="Auto-checkpoint ${timestamp}: ${file_list}"

# Save
datalad save -m "$commit_msg" >/dev/null 2>&1 || exit 0

# Report to terminal (visible after Claude's turn, not shown to Claude)
echo "[datalad] checkpoint ${timestamp}: ${file_list}"

exit 0
