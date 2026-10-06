"""Make the rig folder from your own game files.

    python3 tools/make_rig.py --data "/path/Fallout 4/Data" --nvcs /path/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif

The rig folder has files of Fallout 4 and of the New Vegas compatibility skeleton (NVCS), so
it is not in the repository. This program takes each file from your installed game and from
the skeleton file of the NVCS mod:

    1st_skeleton.hkx    the Fallout 4 first-person skeleton (Fallout4 - Animations.ba2)
    TEMPLATE/*.hkx      the first-person clips of each template weapon (the same archive)
    nvcs_1st.json       the New Vegas first-person skeleton: each node, its parent and its matrix

rig/finger_tips.json (measurements of the two hand meshes) is in the repository.
"""
import argparse
import json
import os
import shutil
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

ANIMATIONS = 'Fallout4 - Animations.ba2'
FIRST_PERSON = 'Meshes/Actors/Character/_1stPerson'


def nvcs_nodes(path):
    """The nodes of the New Vegas skeleton: name, parent and local matrix (16 numbers with 8
    significant digits, the translation last)."""
    import fnvnif
    import numpy as np
    nif = fnvnif.Nif(path)
    nodes = []
    for b, parent, _, _, _ in nif.walk():
        if 'data' in b:
            continue
        # single precision, as the file has it
        m = np.eye(4, dtype=np.float32)
        m[:3, :3] = b['rotation'].astype(np.float32) * np.float32(b['scale'])
        m[:3, 3] = b['translation'].astype(np.float32)
        nodes.append({'name': b['name'], 'parent': parent['name'] if parent is not None else '',
                      'matrix': [float('%.8g' % v) for v in m.T.reshape(-1)]})
    return {'nodes': nodes, 'meshes': []}


def main():
    import ba2
    ap = argparse.ArgumentParser(description='Make the rig folder from your own game files.')
    ap.add_argument('--data', required=True, help='the Data folder of Fallout 4')
    ap.add_argument('--nvcs', required=True, help='Meshes/Characters/_1stPerson/Skeleton.nif of the NVCS mod')
    ap.add_argument('--out', default=os.path.join(ROOT, 'rig'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    archive = ba2.Ba2(os.path.join(a.data, ANIMATIONS))
    with open(os.path.join(a.out, '1st_skeleton.hkx'), 'wb') as f:
        f.write(archive.read(FIRST_PERSON + '/CharacterAssets/skeleton.hkx'))
    print('1st_skeleton.hkx')
    # the clips of each template, with names in lower case
    for name in sorted(os.listdir(os.path.join(ROOT, 'templates'))):
        if not name.endswith('.toml'):
            continue
        t = tomllib.load(open(os.path.join(ROOT, 'templates', name), 'rb'))
        folder = os.path.join(a.out, t['clips'])
        os.makedirs(folder, exist_ok=True)
        prefix = '%s/Animations/%s/' % (FIRST_PERSON, t['game_clips'])
        files = [n for n in archive.find(prefix, '.hkx') if '/' not in n[len(prefix):]]
        if not files:
            raise SystemExit('%s has no clip in %s' % (ANIMATIONS, prefix))
        for n in files:
            with open(os.path.join(folder, os.path.basename(n).lower()), 'wb') as f:
                f.write(archive.read(n))
        print('%s: %d clips' % (t['clips'], len(files)))
    with open(os.path.join(a.out, 'nvcs_1st.json'), 'w') as f:
        json.dump(nvcs_nodes(a.nvcs), f, separators=(',', ':'))
    print('nvcs_1st.json')
    # a rig folder at a different place needs the file of the repository too
    tips = os.path.join(ROOT, 'rig', 'finger_tips.json')
    if os.path.abspath(a.out) != os.path.join(ROOT, 'rig'):
        shutil.copyfile(tips, os.path.join(a.out, 'finger_tips.json'))
        print('finger_tips.json')


if __name__ == '__main__':
    main()
