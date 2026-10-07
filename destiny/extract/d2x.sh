#!/usr/bin/env bash
# Runs the d2x command line with the Python environment of d2x (data/destiny/extract/venv).
# It runs from any working folder; a relative path of an argument is relative to that folder.
# `./port destiny COMMAND` does the same and also checks what the command needs.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # destiny/extract
root="$(cd "${here}/../.." && pwd)"                       # the root of the repository
data="${FO4PORTS_DATA:-${root}/data}"                     # the same rule as portkit/paths.py
python="${data}/destiny/extract/venv/bin/python"
if [[ ! -x "${python}" ]]; then
    echo "d2x: the environment ${python} is missing. Run ./port destiny setup (or destiny/extract/setup.sh) first." >&2
    exit 1
fi
export PYTHONDONTWRITEBYTECODE=1
exec "${python}" "${here}/d2x_cli.py" "$@"
