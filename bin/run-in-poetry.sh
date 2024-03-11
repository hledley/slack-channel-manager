#!/usr/bin/env bash

set -euo pipefail

# Find the directory of this script in the repo.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR/.."

stderr_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" >&2
}

poetry_run_command() {
  "$1" run manager sort | perl -pe 'use POSIX strftime; $_ = strftime("%Y-%m-%d %H:%M:%S", localtime) . " - $_"'
}

# Use `poetry` if it can be found
if command -v poetry &> /dev/null; then
  poetry_run_command poetry
# Brew installs to different places on apple silicon vs. intel, and these
# directories may not be on the path. Check the most likely locations:
elif [ -x /opt/homebrew/bin/poetry ]; then # apple silicon
  poetry_run_command /opt/homebrew/bin/poetry
elif [ -x /usr/local/bin/poetry ]; then # intel
  poetry_run_command /usr/local/bin/poetry
else
  stderr_with_timestamp "Could not find poetry. Install it!" >&2
  exit 1
fi
