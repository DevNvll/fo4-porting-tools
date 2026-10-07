#!/usr/bin/env python3
"""Make one picture with frames of a video at equal steps, with the time of each frame.

    ./port destiny check video-sheet VIDEO OUT.jpg [--count 20] [--columns 5] [--width 384]
    python3 destiny/port/check/video_sheet.py ...          (the same program with no ./port)

The picture has COUNT frames in rows of COLUMNS. Each frame has its time in the video (seconds)
in its upper left corner. Use it to look at a recording of the game test before you use it.
The program needs ffmpeg and ffprobe. destiny/port/check/strip.sh makes one row with no times.
"""
import argparse
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser(description='Make one picture with frames of a video at equal steps, with the time of each frame.')
    ap.add_argument('video')
    ap.add_argument('out', help='the picture (.jpg or .png)')
    ap.add_argument('--count', type=int, default=20, help='the count of frames (default 20)')
    ap.add_argument('--columns', type=int, default=5, help='the count of frames in a row (default 5)')
    ap.add_argument('--width', type=int, default=384, help='the width of a frame in the picture (default 384)')
    a = ap.parse_args()
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video],
                           capture_output=True, text=True)
    if probe.returncode != 0 or not probe.stdout.strip():
        raise SystemExit('ffprobe cannot read %s: %s' % (a.video, probe.stderr.strip()))
    seconds = float(probe.stdout)
    tiles = []
    with tempfile.TemporaryDirectory() as folder:
        frame = os.path.join(folder, 'frame.png')
        for i in range(a.count):
            t = seconds * (i + 0.5) / a.count
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '%.2f' % t, '-i', a.video, '-frames:v', '1',
                            '-vf', 'scale=%d:-1' % a.width, frame], check=True)
            im = Image.open(frame).convert('RGB')
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, 56, 12), fill=(0, 0, 0))
            draw.text((2, 0), '%.1f s' % t, fill=(255, 255, 0))
            tiles.append(im)
    w, h = tiles[0].size
    rows = (a.count + a.columns - 1) // a.columns
    sheet = Image.new('RGB', (w * a.columns, h * rows))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % a.columns) * w, (i // a.columns) * h))
    sheet.save(a.out, quality=85)
    print(a.out, '%.1f s' % seconds)


if __name__ == '__main__':
    sys.exit(main())
