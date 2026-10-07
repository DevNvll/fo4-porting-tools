#!/usr/bin/env python3
"""Convert first-person clips of a Destiny 2 weapon to Fallout 4 clips.

    ./port destiny convert FILE.glb --clip CLIP=NAME [--clip CLIP=NAME ...] [-o OUT] [STEP ...]
    ./port destiny convert FILE.glb --set destiny/port/sets/WEAPON.toml [-o OUT] [STEP ...]
    python3 destiny/port/d2fo4.py ...          (the same program with no ./port)

FILE.glb is a first-person file of d2x or m2x (the rig, the gun, the hands and one animation
for each clip). CLIP is the name of a clip in the file and NAME is the name of the Fallout 4
clip, for example

    ./port destiny convert the_last_word_first_person.glb --clip fp_001_80BC8660=WPNReload -o out

The result is OUT/NAME.hkx for each clip (default OUT: data/destiny/port/out/WEAPON). The
same input gives the same bytes.

In this text, work/ is the work folder of the weapon (default: data/destiny/port/work/WEAPON),
rig/ is data/destiny/port/rig, and tools/, sets/ and templates/ are folders of destiny/port.

A set file can be in any folder. A file or a folder that a set file names (`folder` of
[hand_pose] and of [third], `dyes`, `file` of [model.sight], the files of [model.shaders]) is
beside FILE.glb. `folder` of [third] has one more place: when the folder is not beside
FILE.glb, it is a path below data/destiny/port.

A set file (sets/the_last_word.toml) has the clips of one weapon: the clip of the file for
each Fallout 4 clip, more events, frames of the last pose at the end of a clip, the aim point
of the sight, and the clips that the file does not have (walk, run, jump, gun down, shots). Each of those takes the weapon motion
of the vanilla clip of the template weapon.

Four tables of a set file change the clips of the file before each step (tools/d2bake.py
has the rules; the program writes them to work/NAME/clips.json):

    [hand_pose]     folder = "posed": the folder, beside the file of the gun, with the files
                    of tools/d2pose.py. A clip that has a file there has the tracks of that
                    file: the clip with the left hand in the pose for this gun.
    [gun]           rest = true: the gun is on the grip bone of the right hand, with each part
                    at its rest place. [gun.parts] CLIP = "CLIP2": the gun parts of CLIP move
                    as they do in CLIP2.
    [compose.NAME]  a new clip NAME from the clips of the list `clips`, one after the other
                    ("CLIP*3" is three times the clip). `blend` and `cut`: see tools/d2bake.py.
    [piece_events]  CLIP = [[frame, text], ...]: the events of a clip when it is a part of a
                    clip of [compose]. Each use of the clip gives its events (a frame less than
                    zero is before the first frame of the clip). A Fallout 4 clip from a clip of
                    [compose] has these events and those of [events], and no other event.

    --template  the vanilla weapon that gives the weapon bones, the sound names and the pose
                of the body bones (templates/NAME.toml). Default: revolver44.
    --name      the name of the work folder. Default: the file name with no `_first_person`.
    --work      the work folder. Default: data/destiny/port/work/NAME.
    --hold      CLIP[:FRAME], the hold pose of the weapon: it gives the place of the gun in
                Fallout 4 weapon space. Default: the first frame of the first clip of the file.
    --event     NAME:FRAME=TEXT, an event of a clip in place of, or more than, the events
                that the tools find.
    --skip      a shape of the parts file that is not a collider for the fingers.

The steps, in this order (all steps when none is given):

    bake      evaluate each clip and write the bone matrices in Fallout 4 world space (work/bake)
    parts     put the gun meshes into Fallout 4 weapon space, each on its weapon bone (work/parts.json)
    retarget  move each pose to the Fallout 4 first-person skeleton, in Blender (work/fo4/poses)
    hkx       write the HKX clips and read each one again (work/fo4/hkx)
    install   copy the clips into the output folder

One more step is not in "all steps": name it to run it.

    third     the third-person clips of [third] of the set file: retarget each one to the
              Fallout 4 third-person skeleton (tools/blender/d3retarget.py), write the HKX clip
              (work/third/hkx) and copy it into the folder of --third-output. The source of a
              clip is a file of tools/d2third.py. Its events are those of the first-person
              clip with the same name (work/fo4/hkx), some frames earlier or later: the count
              of frames by which the bolt (or the parts of `align` of [third]) moves later in
              the third-person clip. [third.events]
              of the set file changes or adds events. [third.poses] makes a clip of one pose.
              [third.compose.NAME] makes a source NAME from files of tools/d2third.py, one
              after the other, as [compose] does; [third.piece_events] has their events.
              `silent` of [third]: a list of clips that get no event SoundPlay (see the
              set file of The Chaperone: the game plays the default reload clip on a second
              clip node at the same time as a reload clip with a new name).
              [third.hold_end] NAME = FRAMES: the last pose of the clip NAME on this count
              of more frames at its end. The third-person graph of the game sends reloadEnd
              0.5 s before the end of a reload clip (a trigger of the clip node, 15 frames),
              so a reload clip that moves until its end needs frames after its motion.
              [third.power_armor] NAME = "VANILLA": the clip NAME for a body in power
              armor is a copy of the vanilla clip VANILLA of the template (rig/, the folder
              `third_power_armor_clips`), in the folder power_armor_third_person beside the
              folder of --third-output. A reload clip with a new name needs it: the two
              third-person views have one graph, and esx builds a clip with a new name only
              when the two views have it.
              [third.parts] STATE = "CLIP": the gun parts of the source STATE move against
              the gun as they do in the first-person clip CLIP of work/bake (frame n of the
              one is frame n of the other). This is for a gun whose entity has no clip of
              its parts.

The setting `blender` names the Blender program (the environment variable BLENDER, then
data/config.toml, then blender in the PATH). The Fallout 4 library is fnv/tools of this
repository: its solver, its HKX writer and its rig folder data/fnv/rig (the Fallout 4 skeleton;
PORT_RIG names another folder) are the base of these tools.
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, 'tools')
DATA = paths.data('destiny', 'port')                        # the work files, the results and the rig folder
STEPS = ['bake', 'parts', 'retarget', 'hkx', 'install']
MORE_STEPS = ['third']


def blender_program():
    return paths.require('blender')


def part_shift(first_poses, third_poses, bones):
    """(frames, note): how many frames later the gun parts move in the third-person clip than in
    the first-person clip. For each weapon bone of `bones` that moves against the bone Weapon in
    the two pose files: the first frame with the bone away from its place of the first frame.
    The result is the median of the differences."""
    import numpy as np

    def starts(path):
        d = np.load(path)
        names = [str(n) for n in d['names']]
        gun = np.linalg.inv(d['poses'][:, names.index('Weapon')])
        out = {}
        for i, n in enumerate(names):
            if not n.startswith('Weapon') or n == 'Weapon' or n.startswith('WeaponIK') or n == 'WeaponLeft':
                continue
            rel = gun @ d['poses'][:, i]
            move = np.linalg.norm(rel[:, :3, 3] - rel[0, :3, 3], axis=1)
            turn = np.degrees(np.arccos(np.clip((np.einsum('fij,ij->f', rel[:, :3, :3], rel[0, :3, :3]) - 1.0) / 2.0, -1.0, 1.0)))
            away = np.nonzero((move > 0.1) | (turn > 2.0))[0]
            if len(away):
                out[n] = int(away[0])
        return out
    a, b = starts(first_poses), starts(third_poses)
    common = sorted(set(a) & set(b) & set(bones))
    if not common:
        return 0, 'no part of %s moves in the two clips' % ', '.join(bones)
    diffs = [b[n] - a[n] for n in common]
    return int(round(float(np.median(diffs)))), ', '.join('%s %+d' % (n, b[n] - a[n]) for n in common)


def expand(items):
    """A list of clips where `CLIP*N` is N times the clip, as a plain list."""
    out = []
    for text in items:
        clip, _, count = text.partition('*')
        out += [clip.strip()] * int(count or 1)
    return out


def piece_events(pieces, starts, table, last):
    """--event options of d2hkx.py for the events of the pieces of a clip of [compose]."""
    out, seen = [], set()
    for piece, start in zip(pieces, starts):
        for frame, text in table.get(piece, []):
            out += ['--event', '%d=%s%s' % (min(max(start + frame, 0), last), '+' if text in seen else '', text)]
            seen.add(text)
    return out


def main():
    ap = argparse.ArgumentParser(prog='d2fo4.py', description='Convert first-person clips of a Destiny 2 weapon to Fallout 4 clips.')
    ap.add_argument('file', help='the first-person file (.glb) of d2x or m2x')
    ap.add_argument('steps', nargs='*', help='the steps to run (default: all): ' + ' '.join(STEPS))
    ap.add_argument('--clip', action='append', default=[], metavar='CLIP=NAME')
    ap.add_argument('--set', help='a file with the clips of a weapon (destiny/port/sets/NAME.toml)')
    ap.add_argument('-o', '--output', help='the folder for the clips (default: data/destiny/port/out/NAME)')
    ap.add_argument('--third-output', help='the folder for the third-person clips (default: OUTPUT/third_person)')
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--name', help='the name of the work folder (default: the file name with no _first_person)')
    ap.add_argument('--work', help='the work folder (default: data/destiny/port/work/NAME)')
    ap.add_argument('--hold')
    ap.add_argument('--event', action='append', default=[], metavar='NAME:FRAME=TEXT')
    ap.add_argument('--skip', action='append', default=[])
    a = ap.parse_args()
    for s in a.steps:
        if s not in STEPS + MORE_STEPS:
            raise SystemExit('unknown step %s; the steps are: %s' % (s, ' '.join(STEPS + MORE_STEPS)))
    steps = a.steps or STEPS
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'            # no cache files in the source tree
    source = os.path.abspath(a.file)
    name = a.name or os.path.splitext(os.path.basename(source))[0].replace('_first_person', '')
    work = os.path.abspath(a.work or os.path.join(DATA, 'work', name))
    out = os.path.abspath(a.output or os.path.join(DATA, 'out', name))
    clips = []
    for text in a.clip:
        clip, sep, target = text.partition('=')
        if not sep or not target:
            raise SystemExit('--clip needs CLIP=NAME, for example fp_001_80BC8660=WPNReload')
        clips.append((clip, target))
    events = list(a.event)
    hold_end = {}                                           # Fallout 4 clip -> frames of the last pose at its end
    auto = {}                                               # Fallout 4 automatic fire clip -> clip of one shot
    roles = []                                              # BONE=KIND for each weapon bone with a kind in the set file
    part_options = []                                       # more options of the parts step, from the set file
    sight = []                                              # the options of the sight for the retarget step
    knuckles = []                                           # the options of the hands for the retarget step
    synth = []                                              # (name, pose, vanilla clip, static frame or None, frames, reference clip or None)
    poses = {}                                              # kind -> (clip, frame)
    third = {}                                              # the table [third] of the set file
    rules = {}                                              # the clip rules: the tables [gun] and [compose]
    pieces = {}                                             # the table [piece_events]
    if a.set:
        import tomllib
        with open(a.set, 'rb') as f:
            data = tomllib.load(f)
        a.template = data.get('template', a.template)
        a.hold = a.hold or data.get('hold')
        third = data.get('third', {})
        if data.get('knuckles'):
            knuckles = ['--knuckles', data['knuckles']]
        if data.get('closed_fingers'):
            knuckles += ['--closed-fingers', 'on']
        if data.get('hand_pose'):
            # each clip that has a file of tools/d2pose.py
            posed = os.path.join(os.path.dirname(os.path.abspath(a.file)), data['hand_pose'].get('folder', 'posed'))
            if not os.path.isdir(posed):
                raise SystemExit('%s: the folder %s of [hand_pose] is not there (tools/d2pose.py makes it)' % (a.set, posed))
            rules['tracks'] = {n[:-4]: os.path.join(posed, n) for n in sorted(os.listdir(posed)) if n.endswith('.npz')}
        if data.get('gun'):
            rules['gun'] = data['gun']
        if data.get('compose'):
            rules['compose'] = {clip: dict(spec, clips=expand(spec['clips'])) for clip, spec in data['compose'].items()}
        pieces = data.get('piece_events', {})
        clips += [(clip, target) for target, clip in data.get('clips', {}).items()]
        # automatic fire: the clip of one shot, again at each shot time of the vanilla clip with the same name
        auto = dict(data.get('auto', {}))
        clips += [(clip, target) for target, clip in auto.items()]
        for target, items in data.get('events', {}).items():
            seen = set()
            for frame, text in items:
                # a second event with the same text does not replace the first one
                events.append('%s:%d=%s%s' % (target, frame, '+' if text in seen else '', text))
                seen.add(text)
        hold_end = {target: int(frames) for target, frames in data.get('hold_end', {}).items()}
        roles = ['%s=%s' % item for item in data.get('roles', {}).items()]
        part_options = []
        for item in data.get('bones', {}).items():
            part_options += ['--bone', '%s=%s' % item]
        if data.get('part_rest'):
            part_options += ['--rest', data['part_rest']]
        if data.get('sight'):
            sight = ['--sight', ','.join(repr(float(x)) for x in data['sight']['point'])]
            for clip in data['sight'].get('clips', []):
                sight += ['--sight-clip', clip]
        named = dict(data.get('poses', {}), **{kind: data[key] for kind, key in (('ready', 'hold'), ('sighted', 'sighted')) if data.get(key)})
        for kind, text in named.items():
            clip, _, frame = text.partition(':')
            poses[kind] = (clip, int(frame or 0))
        for target, value in data.get('synth', {}).items():
            if isinstance(value, str):
                value = {'pose': value}
            synth.append((target, value['pose'], value.get('vanilla', target).lower(), None, None, value.get('reference')))
        for target, st in data.get('static', {}).items():
            synth.append((target, st['pose'], st['vanilla'], int(st.get('frame', 0)), int(st.get('frames', 30)), None))
        for target, kind, _, _, _, _ in synth:
            if kind not in poses:
                raise SystemExit('%s: the clip %s needs the pose `%s`' % (a.set, target, 'hold' if kind == 'ready' else kind))
    if not clips and not synth:
        raise SystemExit('give --clip CLIP=NAME or --set FILE')
    sources = []                                            # each clip of the file one time
    for clip in [c for c, _ in clips] + [poses[kind][0] for _, kind, _, _, _, _ in synth]:
        if clip not in sources:
            sources.append(clip)
    total = len(clips) + len(synth)
    bake = os.path.join(work, 'bake')
    parts = os.path.join(work, 'parts.json')
    fo4 = os.path.join(work, 'fo4')
    hkx = os.path.join(fo4, 'hkx')
    rig = os.path.join(DATA, 'rig')
    print('[d2fo4] %s: template %s, %d clips to %s' % (name, a.template, total, out), flush=True)
    # the clip rules for tools/d2bake.py, tools/d2parts.py and the checks
    rules_file = os.path.join(work, 'clips.json')
    rules_option = []
    if rules:
        import json
        os.makedirs(work, exist_ok=True)
        with open(rules_file, 'w') as f:
            json.dump(rules, f, indent=1)
        rules_option = ['--rules', rules_file]
    elif os.path.exists(rules_file):
        os.remove(rules_file)

    def run(args, label, env=None):
        print('[d2fo4] ' + label, flush=True)
        if subprocess.run(args, env=env).returncode != 0:
            raise SystemExit('[d2fo4] the step failed: ' + label)

    def py(script, *args):
        return [sys.executable, os.path.join(TOOLS, script), *args]

    for step in steps:
        if step == 'bake':
            args = []
            for clip in sources:
                args += ['--clip', clip]
            run(py('d2bake.py', source, *args, '--fo4', '--template', a.template, '--rig', rig, '-o', bake, *rules_option),
                'bake %d clips' % len(sources))
        elif step == 'parts':
            args = ['--hold', a.hold] if a.hold else []
            for role in roles:
                args += ['--role', role]
            run(py('d2parts.py', source, '-o', parts, '--template', a.template, *args, *part_options, *rules_option), 'parts')
        elif step == 'retarget':
            import json
            user = os.path.join(work, 'blender-user')
            env = dict(os.environ, BLENDER_USER_CONFIG=user + '/config', BLENDER_USER_SCRIPTS=user + '/scripts',
                       BLENDER_USER_DATAFILES=user + '/datafiles', BLENDER_USER_RESOURCES=user)
            args = [blender_program(), '--background', '--factory-startup', '--python-exit-code', '1',
                    '--python', os.path.join(TOOLS, 'blender', 'd2retarget.py'), '--']
            done = []
            for clip, _ in clips:
                if clip not in done:
                    done.append(clip)
                    args += ['--bake', os.path.join(bake, clip + '.npz')]
            if synth:
                os.makedirs(fo4, exist_ok=True)
                spec = os.path.join(fo4, 'synth.json')
                with open(spec, 'w') as f:
                    json.dump([{'name': target, 'bake': os.path.join(bake, poses[kind][0] + '.npz'), 'frame': poses[kind][1],
                                'kind': kind, 'vanilla': vanilla, 'static': frame, 'frames': frames, 'reference': reference}
                               for target, kind, vanilla, frame, frames, reference in synth], f, indent=1)
                args += ['--synth', spec]
            for s in a.skip:
                args += ['--skip', s]
            run(args + sight + knuckles + ['--parts', parts, '--out', fo4, '--template', a.template, '--rig', rig],
                'retarget %d clips of the file, %d clips with vanilla weapon motion' % (len(done), len(synth)), env)
        elif step == 'hkx':
            sys.path.insert(0, TOOLS)
            from d2template import Template
            template = Template(a.template)
            folder = template.clip_folder(rig)

            def control(target):
                """The vanilla clip that gives the bone Camera Control of a clip of the file: the clip
                with the same name when the reader can read it, else the sighted clip of the template
                for a clip in the sights."""
                import fo4clip
                path = os.path.join(folder, target.lower() + '.hkx')
                try:
                    fo4clip.decode(path, fo4clip.skeleton())
                    return path
                except Exception:
                    if 'sighted' in target.lower() and template.data.get('sighted'):
                        return os.path.join(folder, template.data['sighted'] + '.hkx')
                return None

            def extra(target):
                out = ['--hold-end', str(hold_end[target])] if hold_end.get(target) else []
                if target in auto:
                    out += ['--auto', os.path.join(folder, target.lower() + '.hkx')]
                clip = dict((t, c) for c, t in clips).get(target)
                if clip in rules.get('compose', {}):
                    # a clip of [compose]: the events of its pieces, and no event from the motion of the parts
                    import numpy as np
                    d = np.load(os.path.join(bake, clip + '.npz'))
                    out += ['--no-events'] + piece_events([str(x) for x in d['pieces']], [int(x) for x in d['starts']],
                                                          pieces, d['world'].shape[0] - 2)
                for text in events:
                    which, _, event = text.partition(':')
                    if which == target:
                        out += ['--event', event]
                return out
            for clip, target in clips:
                c = control(target)
                run(py('d2hkx.py', '--poses', os.path.join(fo4, 'poses', clip + '.npz'), '--name', target, '--out', hkx,
                       '--template', a.template, *(['--camera-control', c] if c else []), *extra(target)), 'hkx ' + target)
            for target, _, _, _, _, _ in synth:
                tag = os.path.join(fo4, 'poses', 'synth_' + target)
                run(py('d2hkx.py', '--poses', tag + '.npz', '--name', target, '--out', hkx, '--template', a.template,
                       '--annotations', tag + '.json', *extra(target)), 'hkx ' + target)
        elif step == 'third':
            import json
            if not third.get('clips'):
                raise SystemExit('%s has no table [third.clips]' % (a.set or 'the command'))
            sys.path.insert(0, TOOLS)
            import fo4clip
            import anim_fo4
            # the folder of the files of tools/d2third.py: beside the file of the gun, else below data/destiny/port
            folder = os.path.join(os.path.dirname(source), third.get('folder', 'third_person'))
            if not os.path.isdir(folder):
                folder = os.path.join(DATA, third.get('folder', 'third_person'))
            work3 = os.path.join(work, 'third')
            third_out = os.path.abspath(a.third_output or os.path.join(out, 'third_person'))
            user = os.path.join(work, 'blender-user')
            env = dict(os.environ, BLENDER_USER_CONFIG=user + '/config', BLENDER_USER_SCRIPTS=user + '/scripts',
                       BLENDER_USER_DATAFILES=user + '/datafiles', BLENDER_USER_RESOURCES=user)
            args = [blender_program(), '--background', '--factory-startup', '--python-exit-code', '1',
                    '--python', os.path.join(TOOLS, 'blender', 'd3retarget.py'), '--']
            # a source of [third.compose]: files of tools/d2third.py, one after the other (tools/d2bake.py)
            composed = {}
            for state, spec in third.get('compose', {}).items():
                import numpy as np
                from d2bake import join_world
                names_of = expand(spec['clips'])
                files = [np.load(os.path.join(folder, n + '.npz')) for n in names_of]
                bones = [str(n) for n in files[0]['names']]
                world = join_world([f['world'] for f in files], [int(x) for x in files[0]['parents']], int(spec.get('blend', 0)),
                                   [bones.index(b) for b in spec.get('cut', [])])
                starts = [int(x) for x in np.cumsum([0] + [f['world'].shape[0] - 1 for f in files[:-1]])]
                os.makedirs(os.path.join(work3, 'source'), exist_ok=True)
                composed[state] = (names_of, starts)
                np.savez_compressed(os.path.join(work3, 'source', state + '.npz'), world=world, names=files[0]['names'],
                                    parents=files[0]['parents'], fps=files[0]['fps'])
                print('[d2fo4] %s: %d frames (%s)' % (state, world.shape[0], ', '.join('%s from frame %d' % x for x in zip(names_of, starts))), flush=True)
            # [third.parts]: the gun parts of a source against the gun, from a first-person clip
            moved = set()
            for state, clip in third.get('parts', {}).items():
                import numpy as np
                import d2rig
                d = np.load(os.path.join(work3, 'source' if state in composed else folder, state + '.npz')
                            if state in composed else os.path.join(folder, state + '.npz'))
                first_person = np.load(os.path.join(bake, clip + '.npz'))
                bones = [str(n) for n in d['names']]
                fp_bones = [str(n) for n in first_person['names']]
                world = np.array(d['world'], copy=True)
                gun3, gun1 = bones.index(d2rig.WEAPON), fp_bones.index(d2rig.WEAPON)
                frames = np.minimum(np.arange(world.shape[0]), first_person['world'].shape[0] - 1)
                below = [k for k, p in enumerate(d['parents']) if p == gun3]
                below += [k for k, p in enumerate(d['parents']) if p in below]
                for k in below:
                    if bones[k] not in fp_bones:
                        continue
                    part = np.linalg.inv(first_person['world'][frames, gun1]) @ first_person['world'][frames, fp_bones.index(bones[k])]
                    part[:, :3, 3] /= d2rig.SCALE                       # the bake has game units, the source has meters
                    world[:, k] = world[:, gun3] @ part
                os.makedirs(os.path.join(work3, 'source'), exist_ok=True)
                np.savez_compressed(os.path.join(work3, 'source', state + '.npz'), world=world, names=d['names'], parents=d['parents'], fps=d['fps'])
                moved.add(state)
                print('[d2fo4] %s: the gun parts of the first-person clip %s' % (state, clip), flush=True)
            for target, state in third['clips'].items():
                args += ['--bake', os.path.join(work3, 'source', state + '.npz') if state in composed or state in moved
                         else os.path.join(folder, state + '.npz'), '--name', target]
            if third.get('gun'):
                args += ['--gun', third['gun'], '--blend', str(int(third.get('blend', 8)))]
            if a.hold and third.get('right_hand', 'hold') == 'hold':
                # the right hand has the grip of the first-person hold pose (tools/blender/d3retarget.py)
                clip, _, frame = a.hold.partition(':')
                args += ['--grip', os.path.join(fo4, 'poses', clip + '.npz'), '--grip-frame', frame or '0']
            run(args + ['--parts', parts, '--out', work3, '--template', a.template, '--rig', rig],
                'retarget %d third-person clips' % len(third['clips']), env)
            os.makedirs(third_out, exist_ok=True)
            for target in third['clips']:
                import numpy as np
                more_frames = int(third.get('hold_end', {}).get(target, 0))
                frames = int(np.load(os.path.join(work3, 'poses', target + '.npz'))['poses'].shape[0]) + more_frames
                # The events of the first-person clip with the same name. The two clips of Destiny have
                # the same motion of the gun parts, some frames earlier or later: each event moves by
                # that count of frames (the median, for the parts that move in the two clips, of the
                # first frame with the part away from its place).
                first = os.path.join(hkx, target + '.hkx')
                annotations, shift, note = [], 0, None
                source_clip = dict((t, c) for c, t in clips).get(target)
                state = third['clips'][target]
                if state in composed:
                    note = 'a clip of [third.compose]: the events of its pieces'
                elif os.path.exists(first):
                    clip = anim_fo4.load_fo4_animation(first)
                    if source_clip and os.path.exists(os.path.join(fo4, 'poses', source_clip + '.npz')):
                        # the parts that give the count: `align` of [third], else the bolt of the template
                        from d2template import Template
                        align = third.get('align') or [b for kind, b in Template(a.template).roles.items() if kind == 'bolt']
                        shift, note = part_shift(os.path.join(fo4, 'poses', source_clip + '.npz'), os.path.join(work3, 'poses', target + '.npz'), align)
                    last = (frames - 2) / 30.0
                    annotations = [[round(min(max(x.time + shift / 30.0, 0.0), last), 4), x.text] for x in clip.annotations]
                spec = os.path.join(work3, target + '.events.json')
                with open(spec, 'w') as f:
                    json.dump({'annotations': annotations, 'from': os.path.relpath(first, work) if annotations else None,
                               'frames_later': shift, 'parts': note}, f, indent=1)
                print('[d2fo4] %s: the events of the first-person clip, %d frames later (%s)' % (target, shift, note), flush=True)
                more = []
                seen = set()
                if state in composed:
                    more = piece_events(composed[state][0], composed[state][1], third.get('piece_events', {}), frames - 2)
                    seen = set(text.partition('=')[2].lstrip('+') for text in more[1::2])
                for frame, text in third.get('events', {}).get(target, []):
                    more += ['--event', '%d=%s%s' % (frame, '+' if text in seen else '', text)]
                    seen.add(text)
                if target in third.get('silent', []):
                    # no sound events: the pairs (--event, FRAME=TEXT) and the events of the first-person clip
                    kept = []
                    for option, text in zip(more[0::2], more[1::2]):
                        if not text.partition('=')[2].lstrip('+').startswith('SoundPlay.'):
                            kept += [option, text]
                    more = kept
                    with open(spec) as f:
                        data_of = json.load(f)
                    data_of['annotations'] = [x for x in data_of['annotations'] if not x[1].startswith('SoundPlay.')]
                    with open(spec, 'w') as f:
                        json.dump(data_of, f, indent=1)
                if more_frames:
                    more += ['--hold-end', str(more_frames)]
                run(py('d2hkx.py', '--poses', os.path.join(work3, 'poses', target + '.npz'), '--name', target,
                       '--out', os.path.join(work3, 'hkx'), '--template', a.template, '--annotations', spec, *more), 'hkx ' + target + ' (third person)')
                shutil.copyfile(os.path.join(work3, 'hkx', target + '.hkx'), os.path.join(third_out, target + '.hkx'))
            # a clip that is one pose: a frame of a third-person clip, on two frames
            for target, text in third.get('poses', {}).items():
                import numpy as np
                clip, _, frame = text.partition(':')
                d = np.load(os.path.join(work3, 'poses', clip + '.npz'))
                one = os.path.join(work3, 'poses', target + '.npz')
                pose = np.array(d['poses'][int(frame or 0)], copy=True)
                index = {str(n): i for i, n in enumerate(d['names'])}
                # The bone WeaponIKTargetLMirror of the vanilla pose WPNAssemblyPose is the right hand,
                # mirrored in the space of the gun (x to -x). The game uses it when the left hand
                # holds the gun.
                held = np.linalg.inv(pose[index['Weapon']]) @ pose[index['RArm_Hand']]
                mirror = np.eye(4)
                mirror[:3, :3] = np.diag([-1.0, 1.0, 1.0]) @ held[:3, :3] @ np.diag([1.0, 1.0, -1.0])
                mirror[:3, 3] = held[:3, 3] * [-1.0, 1.0, 1.0]
                pose[index['WeaponIKTargetLMirror']] = pose[index['Weapon']] @ mirror
                np.savez_compressed(one, poses=np.repeat(pose[None], 2, axis=0), names=d['names'], parents=d['parents'], fps=d['fps'])
                run(py('d2hkx.py', '--poses', one, '--name', target, '--out', os.path.join(work3, 'hkx'), '--template', a.template,
                       '--no-events'), 'hkx ' + target + ' (third person, one pose)')
                shutil.copyfile(os.path.join(work3, 'hkx', target + '.hkx'), os.path.join(third_out, target + '.hkx'))
            print('[d2fo4] %d third-person clips in %s' % (len(third['clips']) + len(third.get('poses', {})), third_out))
            if third.get('power_armor'):
                from d2template import Template
                vanilla = os.path.join(rig, Template(a.template).data['third_power_armor_clips'])
                armor_out = os.path.join(os.path.dirname(third_out), 'power_armor_third_person')
                os.makedirs(armor_out, exist_ok=True)
                for target, clip in third['power_armor'].items():
                    shutil.copyfile(os.path.join(vanilla, clip.lower() + '.hkx'), os.path.join(armor_out, target + '.hkx'))
                print('[d2fo4] %d clips of the power armor (copies of vanilla clips) in %s' % (len(third['power_armor']), armor_out))
        elif step == 'install':
            os.makedirs(out, exist_ok=True)
            targets = [t for _, t in clips] + [t for t, _, _, _, _, _ in synth]
            for target in targets:
                shutil.copyfile(os.path.join(hkx, target + '.hkx'), os.path.join(out, target + '.hkx'))
            print('[d2fo4] %d clips in %s' % (len(targets), out))


if __name__ == '__main__':
    main()
