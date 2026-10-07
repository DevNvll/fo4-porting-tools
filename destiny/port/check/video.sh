#!/bin/sh
# Make a video from pictures of check/render.py (all frames): the source at the left, the result at the right.
#   sh destiny/port/check/video.sh DIR CLIP OUT.mp4 VIEW [VIEW2] [RATE]
# With two views, the second view is below the first one. RATE is the frame rate (default 30; 10 is slow motion).
set -e
DIR=$1; CLIP=$2; OUT=$3; V1=$4; V2=$5; RATE=${6:-30}
if [ -z "$V2" ] || [ "$V2" = "-" ]; then
  ffmpeg -v error -y -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V1}_src.png" -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V1}_fo4.png" \
    -filter_complex "[0:v][1:v]hstack=inputs=2,format=yuv420p" -c:v libx264 -crf 18 -r 30 "$OUT"
else
  ffmpeg -v error -y -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V1}_src.png" -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V1}_fo4.png" \
    -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V2}_src.png" -framerate $RATE -i "$DIR/${CLIP}_f%03d_${V2}_fo4.png" \
    -filter_complex "[0:v][1:v][2:v][3:v]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0,format=yuv420p" -c:v libx264 -crf 18 -r 30 "$OUT"
fi
