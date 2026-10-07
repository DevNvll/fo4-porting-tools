#!/bin/sh
# Run a program in Blender with no window: sh fnv/tools/bl.sh SCRIPT.py -- ARGUMENTS
#
# Blender is the setting `blender`: the variable BLENDER, then data/config.toml, then `blender`
# in the PATH (portkit/paths.py). Blender 4.5 is tested.
# The user folders of Blender are in the work folder (PORT_WORK; default: data/fnv/work), so
# Blender does not read and does not change the settings of the user.
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=${FO4PORTS_ROOT:-$(CDPATH= cd -- "$HERE/../.." && pwd)}
B=${BLENDER:-$(python3 "$ROOT/portkit/paths.py" get blender)}
if [ -z "$B" ]; then
    echo "bl.sh: the setting \`blender\` has no value. Give it in data/config.toml or in the variable BLENDER." >&2
    exit 1
fi
U=${PORT_WORK:-${FO4PORTS_DATA:-$ROOT/data}/fnv/work}/blender-user
BLENDER_USER_CONFIG=$U/config BLENDER_USER_SCRIPTS=$U/scripts BLENDER_USER_DATAFILES=$U/datafiles BLENDER_USER_RESOURCES=$U exec "$B" --background --factory-startup --python-exit-code 1 --python "$@"
