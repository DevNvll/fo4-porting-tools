#!/usr/bin/env python3
"""Put the pictures of one frame of destiny/port/check/render.py in one picture: one column for each view.

    ./port destiny check look-sheet DIR CLIP FRAME OUT.jpg VIEW[,VIEW...] [--cell 420]
    python3 destiny/port/check/look_sheet.py ...          (the same program with no ./port)

DIR is the folder of --out of render.py and CLIP is the tag of its pictures (--tag, or the
name of the clip). The upper row is the source and the lower row is the result. The views
are those of render.py (fp, r_thumb, l_thumb, l_palm, gun_left, ...); render.py must have
made each one with the kinds src and fo4.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser(description='Put the pictures of one frame of check/render.py in one picture: one column for each view.')
    ap.add_argument('folder', metavar='DIR', help='the folder with the pictures of render.py')
    ap.add_argument('clip', help='the tag of the pictures (the name of the clip, or --tag of render.py)')
    ap.add_argument('frame', type=int)
    ap.add_argument('out', help='the picture (.jpg or .png)')
    ap.add_argument('views', help='the views, with commas between them')
    ap.add_argument('--cell', type=int, default=420, help='the size of a picture in the sheet (default 420)')
    a = ap.parse_args()
    views = a.views.split(',')
    sheet = Image.new('RGB', (a.cell * len(views), a.cell * 2), (30, 30, 30))
    for x, view in enumerate(views):
        for y, kind in enumerate(('src', 'fo4')):
            path = os.path.join(a.folder, '%s_f%03d_%s_%s.png' % (a.clip, a.frame, view, kind))
            if not os.path.isfile(path):
                raise SystemExit('the picture %s is not there (render.py makes it)' % path)
            im = Image.open(path).convert('RGB')
            im.thumbnail((a.cell, a.cell), Image.LANCZOS)
            sheet.paste(im, (x * a.cell + (a.cell - im.size[0]) // 2, y * a.cell + (a.cell - im.size[1]) // 2))
            ImageDraw.Draw(sheet).text((x * a.cell + 6, y * a.cell + 4), '%s %s' % (view, 'source' if kind == 'src' else 'result'), fill=(255, 255, 0))
    sheet.save(a.out, quality=88)
    print(a.out, sheet.size)


if __name__ == '__main__':
    sys.exit(main())
