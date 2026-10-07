"""Put the clips of each template weapon into the rig folder, from your own game files.

    ./port destiny make-rig [--data "/path/Fallout 4/Data"]
    python3 destiny/port/tools/make_rig.py [--data "/path/Fallout 4/Data"]

The rig folder is data/destiny/port/rig (rig/ in this text). It has files of Fallout 4, so it
is not in git. The default of --data is the setting `fo4_data` (FO4_DATA, or data/config.toml).
This program reads the first-person clips of each template (templates/NAME.toml:
`game_clips` is the folder, or a list of folders, in Fallout4 - Animations.ba2, `clips` is the
folder in rig/) and writes each one with its name in lower case. The archive reader is
fnv/tools/ba2.py.

The Fallout 4 first-person skeleton and the arm meshes come from the rig folder of fnv
(data/fnv/rig): `./port fnv make-rig --nvcs FILE.nif` makes the skeleton, and
`./port fnv make-rig --arm-meshes` makes the arm meshes. The measurements of the hand meshes are in
the source tree: destiny/port/rig/d2_hands.json (tools/d2hands.py) and fnv/rig/finger_tips.json.

For the third-person clips the program also writes rig/third/skeleton.hkx (the skeleton of the
character) and, for a template with `third_game_clips`, the third-person clips of that folder
of the game (Meshes/Actors/Character/Animations/Weapon) into the folder `third_clips` of rig/.
For a template with `third_power_armor_game_clips` it writes the third-person clips of the
body in power armor (Meshes/Actors/PowerArmor/Animations/Weapons) into the folder
`third_power_armor_clips` of rig/.
"""
import argparse
import os
import sys
import tomllib

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fo4clip  # noqa: E402  (adds fnv/tools to the path)

ANIMATIONS = 'Fallout4 - Animations.ba2'
FIRST_PERSON = 'Meshes/Actors/Character/_1stPerson'
THIRD_PERSON = 'Meshes/Actors/Character/Animations/Weapon'
POWER_ARMOR = 'Meshes/Actors/PowerArmor/Animations/Weapons'
SKELETON = 'Meshes/Actors/Character/CharacterAssets/skeleton.hkx'


def main():
    import ba2
    ap = argparse.ArgumentParser(description='Put the clips of each template weapon into the rig folder.')
    ap.add_argument('--data', help='the Data folder of Fallout 4 (default: the setting fo4_data)')
    ap.add_argument('--out', default=paths.data('destiny', 'port', 'rig'), help='the rig folder (default: data/destiny/port/rig)')
    a = ap.parse_args()
    archive = ba2.Ba2(os.path.join(a.data or paths.require('fo4_data'), ANIMATIONS))
    os.makedirs(os.path.join(a.out, 'third'), exist_ok=True)
    with open(os.path.join(a.out, 'third', 'skeleton.hkx'), 'wb') as f:
        f.write(archive.read(SKELETON))
    print('third/skeleton.hkx')
    for name in sorted(os.listdir(os.path.join(ROOT, 'templates'))):
        if not name.endswith('.toml'):
            continue
        with open(os.path.join(ROOT, 'templates', name), 'rb') as f:
            t = tomllib.load(f)
        if 'base' in t:
            continue                                            # it has the clips of its base template
        folder = os.path.join(a.out, t['clips'])
        os.makedirs(folder, exist_ok=True)
        # `game_clips` is one folder or a list of folders. A clip of a later folder replaces the
        # clip with the same name of an earlier one, as the game does for a weapon with a
        # subfolder (the combat rifle: CombatShotgun, then CombatShotgun/CombatRifle).
        game = t['game_clips'] if isinstance(t['game_clips'], list) else [t['game_clips']]
        written = set()
        for sub in game:
            prefix = '%s/Animations/%s/' % (FIRST_PERSON, sub)
            files = [n for n in archive.find(prefix, '.hkx') if '/' not in n[len(prefix):]]
            if not files:
                raise SystemExit('%s has no clip in %s' % (ANIMATIONS, prefix))
            for n in files:
                with open(os.path.join(folder, os.path.basename(n).lower()), 'wb') as f:
                    f.write(archive.read(n))
                written.add(os.path.basename(n).lower())
        print('%s: %d clips' % (t['clips'], len(written)))
        if t.get('third_game_clips'):
            folder = os.path.join(a.out, t['third_clips'])
            os.makedirs(folder, exist_ok=True)
            prefix = '%s/%s/' % (THIRD_PERSON, t['third_game_clips'])
            files = [n for n in archive.find(prefix, '.hkx') if '/' not in n[len(prefix):]]
            if not files:
                raise SystemExit('%s has no clip in %s' % (ANIMATIONS, prefix))
            for n in files:
                with open(os.path.join(folder, os.path.basename(n).lower()), 'wb') as f:
                    f.write(archive.read(n))
            print('%s: %d clips' % (t['third_clips'], len(files)))
        if t.get('third_power_armor_game_clips'):
            folder = os.path.join(a.out, t['third_power_armor_clips'])
            os.makedirs(folder, exist_ok=True)
            prefix = '%s/%s/' % (POWER_ARMOR, t['third_power_armor_game_clips'])
            files = [n for n in archive.find(prefix, '.hkx') if '/' not in n[len(prefix):]]
            if not files:
                raise SystemExit('%s has no clip in %s' % (ANIMATIONS, prefix))
            for n in files:
                with open(os.path.join(folder, os.path.basename(n).lower()), 'wb') as f:
                    f.write(archive.read(n))
            print('%s: %d clips' % (t['third_power_armor_clips'], len(files)))


if __name__ == '__main__':
    main()
