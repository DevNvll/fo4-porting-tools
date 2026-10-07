#!/bin/sh
# Make one picture with frames of a video at equal steps:
#   sh destiny/port/check/strip.sh VIDEO OUT.jpg [COUNT] [WIDTH]
set -e
V=$1; OUT=$2; N=${3:-6}; W=${4:-480}
frames=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$V")
step=$(( (frames + N - 1) / N )); [ $step -lt 1 ] && step=1
ffmpeg -v error -y -i "$V" -vf "select='not(mod(n\,$step))',scale=$W:-1,tile=${N}x1" -frames:v 1 -q:v 3 "$OUT"
