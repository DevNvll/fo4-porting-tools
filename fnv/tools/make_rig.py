"""Make the rig folder from your own game files.

    ./port fnv make-rig --nvcs /path/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif [--data DATA] [--out DIR] [--arm-meshes]
    python3 fnv/tools/make_rig.py ...             the same command with no ./port

The rig folder (data/fnv/rig) has files of Fallout 4 and of the New Vegas compatibility
skeleton (NVCS), so it is not in the repository. This program takes each file from your
installed game and from the skeleton file of the NVCS mod:

    1st_skeleton.hkx    the Fallout 4 first-person skeleton (Fallout4 - Animations.ba2)
    TEMPLATE/*.hkx      the first-person clips of each template weapon (the same archive)
    nvcs_1st.json       the New Vegas first-person skeleton: each node, its parent and its matrix

The Data folder of Fallout 4 is the setting `fo4_data` (the variable FO4_DATA, then
data/config.toml), or --data. The skeleton file of the NVCS mod is --nvcs, or the setting
`nvcs_skeleton` (the variable NVCS_SKELETON, then data/config.toml). With no skeleton file,
the program keeps a nvcs_1st.json that the folder already has.

With --arm-meshes the program also writes the first-person arm meshes of Fallout 4
(Fallout4 - Meshes.ba2):

    1stpersonmalehands.glb, 1stpersonmalebody.glb    the hand mesh and the arm mesh as glTF files
    1st_skeleton_nodes.json                          the nodes of the first-person skeleton model

The conversion of this area does not read these three files. The checks of destiny/port do
(pictures, contact counts, the hand measurements). The program `esx` makes them from the
models of the game, so this option needs the setting `esx` (the variable ESX_BIN, then
data/config.toml, then the PATH).

The program writes only these files. It does not delete a file of the folder.
fnv/rig/finger_tips.json (measurements of the two hand meshes) is in the repository, and each
tool reads it there. It is not a file of the rig folder.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tomllib

sys.dont_write_bytecode = True                # no cache file in the source tree
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

ANIMATIONS = 'Fallout4 - Animations.ba2'
MESHES = 'Fallout4 - Meshes.ba2'
FIRST_PERSON = 'Meshes/Actors/Character/_1stPerson'
# the arm meshes of the first-person view: the model in the archive, and the file name in the rig folder
ARM_MESHES = (('Meshes/Actors/Character/CharacterAssets/1stPersonMaleHands.nif', '1stpersonmalehands'),
              ('Meshes/Actors/Character/CharacterAssets/1stPersonMaleBody.nif', '1stpersonmalebody'))


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


def arm_meshes(data, out):
    """Write the two arm meshes as glTF files and the nodes of the skeleton model. esx reads
    the models of the game; the scratch folder for them is below the data folder."""
    import ba2
    esx = paths.require('esx')
    path = os.path.join(data, MESHES)
    if not os.path.isfile(path):
        raise SystemExit('%s is not there (the mesh archive of Fallout 4)' % path)
    archive = ba2.Ba2(path)
    scratch = paths.data('fnv', 'work', '_make_rig')
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)

    def run(*args):
        r = subprocess.run([esx, *args, '--format', 'json'], cwd=scratch, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit('esx %s failed: %s' % (' '.join(args[:2]), (r.stdout or r.stderr)[:500]))
        return r.stdout

    for name, stem in ARM_MESHES:
        with open(os.path.join(scratch, stem + '.nif'), 'wb') as f:
            f.write(archive.read(name))
        run('nif', 'export', stem + '.nif', '-o', os.path.join(os.path.abspath(out), stem + '.glb'), '--scale', '1.0', '--overwrite')
        print(stem + '.glb')
    with open(os.path.join(scratch, '1st_skeleton.nif'), 'wb') as f:
        f.write(archive.read(FIRST_PERSON + '/CharacterAssets/skeleton.nif'))
    with open(os.path.join(out, '1st_skeleton_nodes.json'), 'w') as f:
        f.write(run('nif', 'shapes', '1st_skeleton.nif'))
    print('1st_skeleton_nodes.json')
    shutil.rmtree(scratch)


def main():
    import ba2
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=paths.setting('fo4_data'),
                    help='the Data folder of Fallout 4 (default: the setting fo4_data)')
    ap.add_argument('--nvcs', default=paths.setting('nvcs_skeleton', env='NVCS_SKELETON'),
                    help='Meshes/Characters/_1stPerson/Skeleton.nif of the NVCS mod (default: the setting nvcs_skeleton)')
    ap.add_argument('--out', default=paths.data('fnv', 'rig'), help='the rig folder (default: data/fnv/rig)')
    ap.add_argument('--arm-meshes', action='store_true',
                    help='also write the arm meshes of Fallout 4 for the checks of destiny/port (needs the setting esx)')
    a = ap.parse_args()
    if not a.data:
        paths.require('fo4_data')                 # stops with advice
    nvcs_file = os.path.join(a.out, 'nvcs_1st.json')
    if not a.nvcs and not os.path.isfile(nvcs_file):
        raise SystemExit('Give --nvcs: the file Meshes/Characters/_1stPerson/Skeleton.nif of the NVCS mod. '
                         'Or give `nvcs_skeleton` in data/config.toml or in the variable NVCS_SKELETON.')
    needed = [(os.path.join(a.data, ANIMATIONS), 'the animation archive of Fallout 4')]
    if a.nvcs:
        needed.append((a.nvcs, 'the skeleton file of the NVCS mod'))
    for path, what in needed:
        if not os.path.isfile(path):
            raise SystemExit('%s is not there (%s)' % (path, what))
    if a.arm_meshes:
        paths.require('esx')                      # stops with advice, before a file is written
    os.makedirs(a.out, exist_ok=True)
    archive = ba2.Ba2(os.path.join(a.data, ANIMATIONS))
    with open(os.path.join(a.out, '1st_skeleton.hkx'), 'wb') as f:
        f.write(archive.read(FIRST_PERSON + '/CharacterAssets/skeleton.hkx'))
    print('1st_skeleton.hkx')
    # the clips of each template, with names in lower case
    templates = paths.repo('fnv', 'templates')
    for name in sorted(os.listdir(templates)):
        if not name.endswith('.toml'):
            continue
        with open(os.path.join(templates, name), 'rb') as f:
            t = tomllib.load(f)
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
    if a.nvcs:
        with open(nvcs_file, 'w') as f:
            json.dump(nvcs_nodes(a.nvcs), f, separators=(',', ':'))
        print('nvcs_1st.json')
    else:
        print('nvcs_1st.json: kept (give --nvcs to make it again)')
    if a.arm_meshes:
        arm_meshes(a.data, a.out)
    print('the rig folder is %s' % a.out)


if __name__ == '__main__':
    main()
