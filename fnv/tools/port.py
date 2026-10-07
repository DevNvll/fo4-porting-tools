"""Convert the first-person animations of a New Vegas weapon mod to Fallout 4.

    ./port fnv convert SOURCE [-o OUT] [--template NAME] [--name NAME] [--work DIR]
    python3 fnv/tools/port.py SOURCE ...          the same command with no ./port

SOURCE is the folder of the extracted mod: the gun model (.nif) and the first-person
animations (.kf). The result is one HKX clip for each first-person clip of a Fallout 4 gun,
in the folder OUT (default: data/fnv/out/NAME). No conversion file is necessary. The
tools find the model, the animations, the gun parts, the clips and their events
(fnv/tools/port_defaults.py).

    --template  the vanilla weapon that gives the weapon bones and the motion of the clips
                that the mod does not have: pistol10mm or smg. Default: pistol10mm when the
                animations have the grip code 1hp, else smg.
    --name      the name of the work folder and of the default output folder, in lower
                case. Default: the name of the model file.
    --work      the work folder. Default: data/fnv/work/NAME.

A conversion file (a TOML file) replaces a value that the tools assume:

    ./port fnv convert CONFIG [STEP ...]

The steps, in this order (all steps when none is given):

    bake      evaluate each source animation and write the node matrices (out/anim/NAME.json)
    parts     put the gun meshes into Fallout 4 weapon space (out/fo4mesh/parts.json)
    retarget  move each pose to the Fallout 4 first-person skeleton (out/fo4/poses)
    synth     make the clips that use the weapon motion of the template weapon
    hkx       write the HKX clips (out/fo4/hkx)
    install   copy the clips into the output folder

`port.py CONFIG show` prints the complete data: the values of the file and each default.
`port.py CONFIG plan` prints the source of each clip and the events of each reload; the bake
step prints the same.

The same input gives the same bytes. The work folder is `work` of the conversion file
(default data/fnv/work/NAME).

The rig folder is data/fnv/rig (`./port fnv make-rig` makes it); PORT_RIG names a different
one. Blender is the setting `blender` (BLENDER, then data/config.toml, then the PATH).
"""
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True                # no cache file in the source tree
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['bake', 'parts', 'retarget', 'synth', 'hkx', 'install']


def from_folder(argv):
    """The animations of a source folder, with no configuration file: write a small file
    (conversion.toml) into the work folder and return its name."""
    import argparse
    import json
    import re
    sys.path.insert(0, HERE)
    import port_defaults
    ap = argparse.ArgumentParser(prog='port.py', description='Convert the first-person animations of a New Vegas weapon mod to Fallout 4.')
    ap.add_argument('source', help='the folder of the extracted mod')
    ap.add_argument('-o', '--output', help='the folder for the HKX clips (default: data/fnv/out/NAME)')
    ap.add_argument('--template', help='pistol10mm or smg (default: by the grip code of the animations)')
    ap.add_argument('--name', help='the name of the work folder and of the default output folder (default: the name of the model file)')
    ap.add_argument('--work', help='the work folder (default: data/fnv/work/NAME)')
    a = ap.parse_args(argv)
    source = os.path.abspath(a.source)
    name = a.name or re.sub(r'[^A-Za-z0-9]', '', os.path.splitext(os.path.basename(port_defaults.find_model(source)))[0]).upper()
    template = a.template
    if template is None:
        folder = port_defaults.find_animations(source)
        if folder is None:
            raise SystemExit('the folder %s has no _1stperson folder with .kf files' % source)
        template = 'pistol10mm' if any(f.lower().startswith('1hp') for f in os.listdir(folder)) else 'smg'
    work = os.path.abspath(a.work) if a.work else paths.data('fnv', 'work', name.lower())
    os.makedirs(work, exist_ok=True)
    out = os.path.abspath(a.output) if a.output else paths.data('fnv', 'out', name.lower())
    config = os.path.join(work, 'conversion.toml')    # not port.toml: that name is the command table of an area
    values = [('name', name), ('template', template), ('source', source), ('output', out)]
    if a.work:
        values.append(('work', work))
    lines = ['# written by fnv/tools/port.py for the folder %s' % source]
    lines += ['%s = %s' % (key, json.dumps(value)) for key, value in values]
    with open(config, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('[port] %s: template %s, clips to %s' % (name, template, out), flush=True)
    return config


def check_rig(cfg):
    """Stop when the rig folder does not have the files that each step reads. A rig folder with
    no clip of the template gives a shorter clip list and no error, so the check is here."""
    need = ['1st_skeleton.hkx', 'nvcs_1st.json', os.path.join(cfg.TEMPLATE['clips'], cfg.TEMPLATE['synth']['ready'] + '.hkx')]
    missing = [n for n in need if not os.path.isfile(os.path.join(cfg.RIG, n))]
    if missing:
        raise SystemExit('[port] the rig folder %s does not have: %s\n'
                         '[port] make it one time from your own files: '
                         './port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif' % (cfg.RIG, ', '.join(missing)))
    if not os.path.isfile(cfg.TIPS):
        raise SystemExit('[port] the file %s is not there (measurements of the two hand meshes; it is a file of the repository)' % cfg.TIPS)


def blender_program():
    """The Blender program of the settings. Stops with advice when there is none."""
    b = paths.require('blender')
    if not (os.path.isfile(b) or shutil.which(b)):
        raise SystemExit('[port] the Blender program %s is not there. Give `blender` in data/config.toml or in the variable BLENDER.' % b)
    return b


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'   # the steps write no cache file into the source tree
    if os.path.isdir(sys.argv[1]):
        config, given = from_folder(sys.argv[1:]), []
    elif not os.path.isfile(sys.argv[1]):
        raise SystemExit('[port] %s is not a folder and not a conversion file' % sys.argv[1])
    else:
        config, given = sys.argv[1], sys.argv[2:]
    os.environ['PORT_CONFIG'] = os.path.abspath(config)
    sys.path.insert(0, HERE)
    import port_config as cfg
    import port_clips
    check_rig(cfg)
    os.environ['PORT_WORK'] = cfg.WORK
    os.environ['PORT_CHILD'] = '1'                # a step does not print the notices of the file again
    steps = given or STEPS
    if steps == ['show']:
        # the complete data: the file and each default
        import port_defaults
        print(port_defaults.dump({k: v for k, v in cfg.D.items() if k != 'assumed_clips'}), end='')
        return
    for s in steps:
        if s not in STEPS and s != 'plan':
            raise SystemExit('unknown step %s; the steps are: %s, and show, plan' % (s, ' '.join(STEPS)))
    src = cfg.D['source']
    anim = os.path.join(cfg.OUT, 'anim')
    parts = os.path.join(cfg.OUT, 'fo4mesh', 'parts.json')
    fo4 = os.path.join(cfg.OUT, 'fo4')
    hkx = os.path.join(fo4, 'hkx')
    clips = port_clips.clips()
    # the pose files that the clips and the synth step use
    scenes = []
    for c in clips.values():
        for scene, _, _ in c['parts']:
            if not scene.startswith('synth_') and scene not in scenes:
                scenes.append(scene)
    for kind in ('ready', 'sighted'):
        b = cfg.D.get('synth', {}).get(kind, {}).get('bake')
        if b and b not in scenes:
            scenes.append(b)
    if steps == ['plan']:
        # what the tools assume for the clips: the source of each clip and the events of each reload
        for name, source in cfg.D.get('assumed_clips', {}).items():
            print('[port] %-22s <- %s' % (name, source))
        for name, c in cfg.D.get('clips', {}).items():
            if name.startswith('WPNReload') and c.get('events'):
                end = [f for f, t in c['events'] if t == 'reloadEnd']
                print('[port] %s events: %s' % (name, ', '.join('%d %s' % (f, t.split('.')[-1].replace('{sound}', '')) for f, t in c['events'])))
                if end:
                    print('[port] %s ends at %.4f s' % (name, end[0] / 30.0))
        return

    def run(args, label):
        print('[port] ' + label, flush=True)
        r = subprocess.run(args)
        if r.returncode != 0:
            raise SystemExit('[port] the step failed: ' + label)

    def py(script, *args):
        return [sys.executable, os.path.join(HERE, script), *args]

    def blender(script, *args):
        return ['sh', os.path.join(HERE, 'bl.sh'), os.path.join(HERE, 'blender', script), '--', *args]

    if 'retarget' in steps or ('synth' in steps and cfg.D.get('synth')):
        os.environ['BLENDER'] = blender_program()  # bl.sh reads this variable
    for step in steps:
        if step == 'bake':
            os.makedirs(anim, exist_ok=True)
            for name, kf in src['animations'].items():
                run(py('kfbake.py', kf, '--model', src['model'], '-o', os.path.join(anim, name + '.json')), 'bake ' + name)
            subprocess.run([sys.executable, os.path.abspath(__file__), os.environ['PORT_CONFIG'], 'plan'])
        elif step == 'parts':
            run(py('gun_parts.py', '-o', parts), 'parts')
        elif step == 'retarget':
            args = []
            for name in scenes:
                args += ['--bake', os.path.join(anim, name + '.json')]
            run(blender('retarget.py', *args, '--out', fo4), 'retarget %d pose files' % len(scenes))
        elif step == 'synth':
            if cfg.D.get('synth'):
                run(blender('synth.py', '--out', fo4), 'synth')
        elif step == 'hkx':
            run(py('port_hkx.py', '--poses', os.path.join(fo4, 'poses'), '--out', hkx), 'hkx')
        elif step == 'install':
            out = cfg.path(cfg.D['output'])
            os.makedirs(out, exist_ok=True)
            for name in clips:
                shutil.copyfile(os.path.join(hkx, name + '.hkx'), os.path.join(out, name + '.hkx'))
            print('[port] %d clips in %s' % (len(clips), out))


if __name__ == '__main__':
    main()
