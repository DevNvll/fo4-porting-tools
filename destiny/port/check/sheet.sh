#!/bin/sh
# Put pictures of check/render.py beside each other: for each frame, the source above the result.
#   sh destiny/port/check/sheet.sh DIR CLIP VIEW "0 10 20" OUT.jpg [WIDTH_OF_A_PICTURE]
# A row has the pictures of the frames; the upper row is the source, the lower row is the result.
set -e
if [ $# -lt 5 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; [ $# -ge 1 ] && [ "${1#-}" != "$1" ] && exit 0; exit 2; fi
DIR=$1; CLIP=$2; VIEW=$3; FRAMES=$4; OUT=$5; W=${6:-480}
n=0
set --
for kind in src fo4; do
  for f in $FRAMES; do
    set -- "$@" -i "$DIR/${CLIP}_f$(printf %03d $f)_${VIEW}_${kind}.png"; n=$((n+1))
  done
done
cols=$((n/2))
ffmpeg -v error -y "$@" -filter_complex "$(i=0; while [ $i -lt $n ]; do printf '[%d:v]scale=%d:-1[s%d];' $i $W $i; i=$((i+1)); done; i=0; while [ $i -lt $n ]; do printf '[s%d]' $i; i=$((i+1)); done)xstack=inputs=$n:grid=${cols}x2" -q:v 2 "$OUT"
