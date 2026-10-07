#!/bin/sh
# Make one picture with frames of a video at equal steps:
#   sh destiny/port/check/strip.sh VIDEO OUT.jpg [COUNT] [WIDTH]
set -e
if [ $# -lt 2 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then sed -n '2,3p' "$0" | sed 's/^# \{0,1\}//'; [ $# -ge 1 ] && [ "${1#-}" != "$1" ] && exit 0; exit 2; fi
V=$1; OUT=$2; N=${3:-6}; W=${4:-480}
frames=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$V")
step=$(( (frames + N - 1) / N )); [ $step -lt 1 ] && step=1
ffmpeg -v error -y -i "$V" -vf "select='not(mod(n\,$step))',scale=$W:-1,tile=${N}x1" -frames:v 1 -q:v 3 "$OUT"
