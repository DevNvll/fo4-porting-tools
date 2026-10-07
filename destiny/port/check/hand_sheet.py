#!/usr/bin/env python3
"""Put pictures of one hand before and after a change in one picture.

    ./port destiny check hand-sheet --clip CLIP --before DIR --after DIR --out OUT.jpg
        [--before-game PNG --after-game PNG] [--views l_thumb,l_front] [--frame 0]
        [--before-label TEXT] [--after-label TEXT] [--crop X0,Y0,X1,Y1]
    python3 destiny/port/check/hand_sheet.py ...          (the same program with no ./port)

The change is, for example, the pose clip of a gun ([hand_pose] of a set file): the left hand
before the pose clip and with it. --before and --after are two folders with pictures of
destiny/port/check/render.py for the same clip and frame (--out of render.py; CLIP is the tag
of the pictures). The lower row has the result (the Fallout 4 hand) of each view, first from
the folder of --before, then from the folder of --after.

With --before-game and --after-game (two game pictures of 1280 x 720, of
destiny/port/check/game_sight.py: hip.png) the upper row has the part of each game picture
that --crop names (default: 440,248,1280,720, the lower right part, where the left hand is
at the hip).
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

CELL = 420


def main():
    ap = argparse.ArgumentParser(description='Put pictures of one hand before and after a change in one picture.')
    ap.add_argument('--clip', required=True, help='the tag of the pictures of render.py (the name of the clip, or --tag)')
    ap.add_argument('--before', required=True, metavar='DIR', help='the folder with the pictures of render.py before the change')
    ap.add_argument('--after', required=True, metavar='DIR', help='the folder with the pictures after the change')
    ap.add_argument('--out', required=True, help='the picture (.jpg or .png)')
    ap.add_argument('--before-game', metavar='PNG', help='a game picture before the change')
    ap.add_argument('--after-game', metavar='PNG', help='a game picture after the change')
    ap.add_argument('--views', default='l_thumb,l_front', help='the views of render.py (default l_thumb,l_front)')
    ap.add_argument('--frame', type=int, default=0)
    ap.add_argument('--before-label', default='before')
    ap.add_argument('--after-label', default='with the pose clip')
    ap.add_argument('--crop', default='440,248,1280,720', help='the part of a game picture: X0,Y0,X1,Y1')
    a = ap.parse_args()
    if bool(a.before_game) != bool(a.after_game):
        raise SystemExit('give --before-game and --after-game, or none of the two')
    views = a.views.split(',')
    names = {'l_thumb': 'from the side of the thumb', 'r_thumb': 'from the side of the thumb', 'l_front': 'from the front',
             'r_front': 'from the front', 'l_palm': 'from the palm', 'r_palm': 'from the palm', 'l_back': 'from the back',
             'r_back': 'from the back', 'l_under': 'from below', 'r_under': 'from below'}
    width = CELL * len(views) * 2
    crop = tuple(int(v) for v in a.crop.split(','))
    half = width // 2
    top = half * (crop[3] - crop[1]) // (crop[2] - crop[0]) if a.before_game else 0
    sheet = Image.new('RGB', (width, top + CELL), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)

    def label(x, y, text):
        draw.rectangle((x, y, x + 8 + 7 * len(text), y + 17), fill=(0, 0, 0))
        draw.text((x + 5, y + 3), text, fill=(255, 255, 0))

    if a.before_game:
        for x, (text, path) in enumerate((('the game, ' + a.before_label, a.before_game), ('the game, ' + a.after_label, a.after_game))):
            im = Image.open(path).convert('RGB').crop(crop).resize((half, top), Image.LANCZOS)
            sheet.paste(im, (x * half, 0))
            label(x * half, 0, text)
    cells = [(a.before_label, a.before, view) for view in views] + [(a.after_label, a.after, view) for view in views]
    for x, (text, folder, view) in enumerate(cells):
        path = os.path.join(folder, '%s_f%03d_%s_fo4.png' % (a.clip, a.frame, view))
        if not os.path.isfile(path):
            raise SystemExit('the picture %s is not there (render.py makes it)' % path)
        im = Image.open(path).convert('RGB').resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(im, (x * CELL, top))
        label(x * CELL, top, '%s, %s' % (text, names.get(view, view)))
    sheet.save(a.out, quality=90)
    print(a.out, sheet.size)


if __name__ == '__main__':
    sys.exit(main())
