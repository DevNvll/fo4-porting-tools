"""Convert the first-person animations of a New Vegas weapon mod to Fallout 4.

    python3 tools/port.py SOURCE [-o OUT] [--template NAME] [--name NAME]

SOURCE is the folder of the extracted mod: the gun model (.nif) and the first-person
animations (.kf). The result is one HKX clip for each first-person clip of a Fallout 4 gun,
in the folder OUT (default: NAME-fo4 in the current folder). No configuration file is
necessary. The tools find the model, the animations, the gun parts, the clips and their
events (tools/port_defaults.py).

    --template  the vanilla weapon that gives the weapon bones and the motion of the clips
                that the mod does not have: pistol10mm or smg. Default: pistol10mm when the
                animations have the grip code 1hp, else smg.
    --name      the name of the work folder and of the default output folder. Default: the
                name of the model file.

A configuration file replaces a value that the tools assume:

    python3 tools/port.py CONFIG [STEP ...]

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

The same input gives the same bytes. The work folder is `work` of the configuration file
(default /tmp/NAME-port).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ['bake', 'parts', 'retarget', 'synth', 'hkx', 'install']


def from_folder(argv):
    """The animations of a source folder, with no configuration file: write a small file into
    the work folder and return its name."""
    import argparse
    import json
    import re
    sys.path.insert(0, HERE)
    import port_defaults
    ap = argparse.ArgumentParser(prog='port.py', description='Convert the first-person animations of a New Vegas weapon mod to Fallout 4.')
    ap.add_argument('source', help='the folder of the extracted mod')
    ap.add_argument('-o', '--output', help='the folder for the HKX clips (default: NAME-fo4 in the current folder)')
    ap.add_argument('--template', help='pistol10mm or smg (default: by the grip code of the animations)')
    ap.add_argument('--name', help='the name of the work folder (default: the name of the model file)')
    a = ap.parse_args(argv)
    source = os.path.abspath(a.source)
    name = a.name or re.sub(r'[^A-Za-z0-9]', '', os.path.splitext(os.path.basename(port_defaults.find_model(source)))[0]).upper()
    template = a.template
    if template is None:
        folder = port_defaults.find_animations(source)
        if folder is None:
            raise SystemExit('the folder %s has no _1stperson folder with .kf files' % source)
        template = 'pistol10mm' if any(f.lower().startswith('1hp') for f in os.listdir(folder)) else 'smg'
    work = '/tmp/%s-port' % name.lower()
    os.makedirs(work, exist_ok=True)
    out = os.path.abspath(a.output or name + '-fo4')
    config = os.path.join(work, 'port.toml')
    lines = ['# written by tools/port.py for the folder %s' % source]
    lines += ['%s = %s' % (key, json.dumps(value)) for key, value in (('name', name), ('template', template), ('source', source), ('output', out))]
    with open(config, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('[port] %s: template %s, clips to %s' % (name, template, out), flush=True)
    return config


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        raise SystemExit(__doc__)
    if os.path.isdir(sys.argv[1]):
        config, given = from_folder(sys.argv[1:]), []
    else:
        config, given = sys.argv[1], sys.argv[2:]
    os.environ['PORT_CONFIG'] = os.path.abspath(config)
    sys.path.insert(0, HERE)
    import port_config as cfg
    import port_clips
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
