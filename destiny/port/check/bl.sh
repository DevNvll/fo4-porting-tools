#!/bin/sh
# Run a check program in Blender with no window:
#   sh destiny/port/check/bl.sh destiny/port/check/SCRIPT.py -- ARGUMENTS
# BLENDER names the Blender program. With no BLENDER it is the setting `blender` of
# portkit (data/config.toml, then blender in the PATH). D2FO4_WORK names the folder for the
# user folders of Blender (default: the folder for temporary files).
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
B=${BLENDER:-$(python3 "$ROOT/portkit/paths.py" get blender)}
if [ -z "$B" ]; then
  echo "bl.sh: the setting blender has no value. Give it in data/config.toml or in BLENDER (./port doctor shows each setting)." >&2
  exit 1
fi
U=${D2FO4_WORK:-${TMPDIR:-/tmp}}/blender-user
BLENDER_USER_CONFIG=$U/config BLENDER_USER_SCRIPTS=$U/scripts BLENDER_USER_DATAFILES=$U/datafiles BLENDER_USER_RESOURCES=$U exec "$B" --background --factory-startup --python-exit-code 1 --python "$@"
