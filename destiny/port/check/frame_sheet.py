#!/usr/bin/env python3
"""Put each frame of the pictures of destiny/port/check/render.py in one picture, for one view.

    ./port destiny check frame-sheet DIR TAG OUT.jpg [--columns 7] [--view fp]
    python3 destiny/port/check/frame_sheet.py ...          (the same program with no ./port)

DIR is the folder of --out of render.py and TAG is the tag of its pictures (--tag, or the
name of the clip). The picture has one cell for each frame that DIR has for the view: the
source above the result (or the result only, when render.py made no picture of the source).
destiny/port/check/sheet.sh does the same for a list of frames that you give.
"""
import argparse
import glob
import os
import re
import sys

from PIL import Image


def main():
    ap = argparse.ArgumentParser(description='Put each frame of the pictures of check/render.py in one picture, for one view.')
    ap.add_argument('folder', metavar='DIR', help='the folder with the pictures of render.py')
    ap.add_argument('tag', help='the tag of the pictures (the name of the clip, or --tag of render.py)')
    ap.add_argument('out', help='the picture (.jpg or .png)')
    ap.add_argument('--columns', type=int, default=7, help='the count of frames in a row (default 7)')
    ap.add_argument('--view', default='fp', help='the view of render.py (default fp)')
    a = ap.parse_args()
    name = os.path.join(a.folder, glob.escape(a.tag) + '_f%s_' + a.view + '_%s.png')
    frames = sorted({int(re.search(r'_f(\d+)_', os.path.basename(p)[len(a.tag):]).group(1)) for p in glob.glob(name % ('*', 'fo4'))})
    if not frames:
        raise SystemExit('%s has no picture %s_fNNN_%s_fo4.png' % (a.folder, a.tag, a.view))
    name = os.path.join(a.folder, a.tag + '_f%03d_' + a.view + '_%s.png')
    tiles = []
    for f in frames:
        pair = [Image.open(name % (f, kind)).convert('RGB') for kind in ('src', 'fo4') if os.path.exists(name % (f, kind))]
        w, h = pair[0].size
        tile = Image.new('RGB', (w, h * len(pair)))
        for i, picture in enumerate(pair):
            tile.paste(picture, (0, h * i))
        tiles.append(tile)
    w, h = tiles[0].size
    rows = (len(tiles) + a.columns - 1) // a.columns
    sheet = Image.new('RGB', (w * a.columns, h * rows))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % a.columns) * w, (i // a.columns) * h))
    sheet.save(a.out, quality=88)
    print(a.out, sheet.size)


if __name__ == '__main__':
    sys.exit(main())
