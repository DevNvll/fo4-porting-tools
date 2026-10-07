"""Command line: python -m d2x <command>.

Run it with the Python environment of d2x and with `destiny/extract` in PYTHONPATH:
`./port destiny COMMAND`, or `destiny/extract/d2x.sh COMMAND`.
"""
import argparse
import sys

from .pkg import DEFAULT_OUT, DEFAULT_VERSION, PackageManager


def _manager(args):
    return PackageManager(args.packages, args.version)


def _resolve(inv, query):
    """Item hashes for a query: a number, an exact name, or part of a name."""
    if query.isdigit():
        return [int(query)]
    matches = inv.find(query)
    with_pattern = [h for h in matches if inv.item(h).pattern_index >= 0]
    exact = [h for h in with_pattern if inv.names()[h].lower() == query.lower()]
    return exact or with_pattern


def command_find(args):
    from .investment import Investment
    inv = Investment(_manager(args))
    rows = inv.find(args.text)
    if not rows:
        print(f'No item name contains {args.text!r} in this game build.')
        return 1
    for item_hash in rows:
        item = inv.item(item_hash)
        pattern = inv.pattern(item.pattern_index)
        entity = f'{pattern.entity:08X}' if pattern and pattern.entity else '-'
        print(f'{item_hash:>10}  pattern_entity={entity:8}  {item.name}')
    return 0


def command_extract(args):
    from .export import extract_weapon
    from .investment import Investment
    pm = _manager(args)
    inv = Investment(pm)
    status = 0
    for query in args.items:
        hashes = _resolve(inv, query)
        if not hashes:
            print(f'{query!r}: no weapon with this name is in this game build.', file=sys.stderr)
            status = 1
            continue
        if len(hashes) > 1 and not args.all:
            print(f'{query!r}: {len(hashes)} weapons match. The first one is used; use --all for all.')
            hashes = hashes[:1]
        arms = []
        for arm_query in args.arms:
            found = [int(arm_query)] if arm_query.isdigit() else [
                h for h in inv.find(arm_query) if inv.item(h).art_arrangement_indices]
            exact = [h for h in found if inv.names().get(h, '').lower() == arm_query.lower()]
            if not found:
                print(f'--arms {arm_query!r}: no item with art in this game build.', file=sys.stderr)
                status = 1
                continue
            arms.append((exact or found)[0])
        for item_hash in hashes:
            stages = (0, 1, 2, 6, 7) if args.transparent else (0,)
            extract_weapon(pm, inv, item_hash, args.out, stages=stages, arms=arms, feminine=args.feminine)
    return status


def command_check(args):
    from .blender import check, find_blender
    print(f'Blender: {find_blender()}')
    status = 0
    for glb in args.files:
        report = check(glb, args.out, clips=args.clips, view=args.view, clip_names=args.clip,
                       frames=args.frames, hide=args.hide, sheet=args.sheet)
        problems = report['problems']
        print(f'{glb}: {len(report["meshes"])} meshes, {report.get("bones", 0)} bones, '
              f'{len(report["actions"])} actions, {len(report["renders"])} renders, '
              f'{"NO PROBLEMS" if not problems else "PROBLEMS: " + "; ".join(problems)}')
        if report.get('sheet_image'):
            print(f'  contact sheet: {report["sheet_image"]}')
        status |= 1 if problems else 0
    return status


def _clip_list(args):
    clips = []
    for text in args.clip:
        text, _, repeat = text.partition('@')
        name, _, label = text.partition('=')
        clips.append((name, label or name, int(repeat or 1)))
    return clips


def command_video(args):
    from .blender import strip_sheet, video
    clips = _clip_list(args)
    if args.out.suffix.lower() == '.png':
        result = strip_sheet(args.file, clips, args.out, view=args.view, columns=args.columns)
    else:
        result = video(args.file, clips, args.out, view=args.view, resolution=(args.width, args.width * 9 // 16))
    print(result)
    return 1 if result['missing'] else 0


def command_tag(args):
    pm = _manager(args)
    for text in args.tags:
        tag = int(text, 16)
        entry = pm.entry(tag)
        if entry is None:
            print(f'{tag:08X}: not found')
            continue
        data = pm.read(tag)
        target = args.out / f'{tag:08X}.bin'
        args.out.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f'{tag:08X}: class/reference {int(entry["reference"]):08X}, type {entry["type"]}/{entry["subtype"]}, '
              f'{len(data)} bytes, {pm.pkg_name(tag)} -> {target}')
    return 0


def main(argv=None):
    from pathlib import Path
    parser = argparse.ArgumentParser(
        prog='d2x', description='Destiny 2 (Tiger engine): export a weapon as glTF files.',
        epilog='The default output folder is data/destiny/extract/out. '
               'The game folder is the setting destiny_game (data/config.toml, or D2X_GAME).')
    # The package options are correct before the command and after it.
    packages_help = ('the packages folder of the game (default: D2X_PACKAGES, '
                     'or the folder packages of the setting destiny_game)')
    version_help = 'tiger-pkg version code (default: D2X_VERSION, or d2_sk)'
    parser.add_argument('--packages', default=None, help=packages_help)
    parser.add_argument('--version', default=DEFAULT_VERSION, help=version_help)
    game = argparse.ArgumentParser(add_help=False)
    game.add_argument('--packages', default=argparse.SUPPRESS, help=packages_help)
    game.add_argument('--version', default=argparse.SUPPRESS, help=version_help)
    commands = parser.add_subparsers(dest='command', required=True)

    find = commands.add_parser('find', parents=[game], help='search item names',
                               description='List the items whose name contains TEXT: item hash, pattern entity, name.')
    find.add_argument('text')
    find.set_defaults(run=command_find)

    extract = commands.add_parser('extract', parents=[game], help='extract weapons to .glb',
                                  description='Export weapons: the model, the textures, the rigs and the clips as '
                                              'glTF files with a manifest, in OUT/<weapon>/.')
    extract.add_argument('items', nargs='+', help='item name or item hash')
    extract.add_argument('--out', type=Path, default=DEFAULT_OUT,
                         help='output folder (default: data/destiny/extract/out)')
    extract.add_argument('--all', action='store_true', help='extract all items that match the name')
    extract.add_argument('--transparent', action='store_true', help='also export decal and transparent parts')
    extract.add_argument('--arms', action='append', default=[], metavar='ARMOR',
                         help='armor item (name or hash) to add to the first-person rig; can repeat')
    extract.add_argument('--feminine', action='store_true', help='use the feminine armor meshes')
    extract.set_defaults(run=command_extract)

    check = commands.add_parser('check', help='import .glb files in Blender, validate, render previews',
                                description='Import .glb files in Blender, do the checks, and render previews. '
                                            'Blender is the setting blender (data/config.toml, or BLENDER).')
    check.add_argument('files', nargs='+', type=Path)
    check.add_argument('--out', type=Path, default=None, help='preview folder (default: preview/ next to the file)')
    check.add_argument('--view', default='side', choices=['side', 'right', 'front', 'back', 'fp'])
    check.add_argument('--clips', type=int, default=0, help='render the middle frame of the first N clips')
    check.add_argument('--clip', action='append', default=[], help='render a frame strip of this clip')
    check.add_argument('--frames', type=int, default=6)
    check.add_argument('--hide', action='append', default=[], help='hide meshes whose name contains this text')
    check.add_argument('--sheet', action='store_true', help='contact sheet with all clips')
    check.set_defaults(run=command_check)

    video = commands.add_parser('video', help='render clips to one .mp4 video, or to a .png frame sheet',
                                description='Render clips of a .glb file from the first-person camera. '
                                            'Blender is the setting blender; a video also needs ffmpeg.')
    video.add_argument('file', type=Path)
    video.add_argument('--clip', action='append', required=True, metavar='NAME[=LABEL][@N]',
                       help='clip name (or its start), an optional label, and N plays of the clip; can repeat')
    video.add_argument('--out', type=Path, required=True, help='.mp4 for a video, .png for a sheet')
    video.add_argument('--view', default='fp', choices=['fp', 'side', 'front'])
    video.add_argument('--width', type=int, default=1280)
    video.add_argument('--columns', type=int, default=8, help='frames for each clip in a sheet')
    video.set_defaults(run=command_video)

    tag = commands.add_parser('tag', parents=[game], help='unpack raw tags by hash',
                              description='Write the raw data of package entries (for example 80BC8633) to files.')
    tag.add_argument('tags', nargs='+')
    tag.add_argument('--out', type=Path, default=DEFAULT_OUT / 'raw',
                     help='output folder (default: data/destiny/extract/out/raw)')
    tag.set_defaults(run=command_tag)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except FileNotFoundError as error:      # a thing of the setup or of the settings is missing
        print(f'd2x: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
