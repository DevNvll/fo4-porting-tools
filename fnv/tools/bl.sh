#!/bin/sh
# Run Blender with no window and with its user folders in the work folder (PORT_WORK).
# BLENDER names the Blender program (default: blender in the PATH). Blender 4.5 is tested.
B=${BLENDER:-blender}
U=${PORT_WORK:-/tmp}/blender-user
BLENDER_USER_CONFIG=$U/config BLENDER_USER_SCRIPTS=$U/scripts BLENDER_USER_DATAFILES=$U/datafiles BLENDER_USER_RESOURCES=$U exec "$B" --background --factory-startup --python-exit-code 1 --python "$@"
