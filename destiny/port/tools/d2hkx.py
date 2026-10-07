"""Write a Fallout 4 HKX clip from retargeted poses (tools/blender/d2retarget.py).

    python3 destiny/port/tools/d2hkx.py --poses WORK/fo4/poses/CLIP.npz --name WPNReload --out DIR
        [--template revolver44] [--event FRAME=TEXT ...] [--no-events] [--hold-end FRAMES]

WORK is the work folder of the weapon (data/destiny/port/work/NAME). A pose file has the world
matrix of each Fallout 4 bone for each frame. The writer and the reader of the clip are
fnv/tools/port_hkx.py and fnv/tools/anim_fo4.py. The program reads the file again and compares
it with the poses.

The events (annotations) of a clip come from its name and from the motion of the gun parts:

    WPNReload...   a revolver (the template has no role `magazine`):
                   SoundPlay.<sound>ReloadBoltOpen    the first frame with the crane away from its place
                   SoundPlay.<sound>ReloadMagIn       the last frame with the rounds away from the cylinder
                   SoundPlay.<sound>ReloadBoltClose   the last frame with the crane away from its place
                   reloadComplete                     2 frames after the later of these two
                   SoundPlay.<sound>ReloadCharge      the first frame with the hammer away from its place, after that
                   a gun with a magazine (the template has the role `magazine`):
                   SoundPlay.<sound>ReloadMagOut      the first frame with the magazine away from its place
                   SoundPlay.<sound>ReloadMagIn       the last frame with the magazine away from its place
                   reloadComplete                     2 frames after that
                   SoundPlay.<sound>ReloadBoltOpen    the first frame with the bolt away from its place
                   SoundPlay.<sound>ReloadBoltClose   the last frame with the bolt away from its place
                   the two kinds:
                   initiateStart, reloadEnd           when the left hand is back at its place of the last frame
    WPNFire...     weaponFire at frame 0

In a reload event <sound> is `reload_sound` of the template when the template has it (the
combat rifle has the reload sounds of the combat shotgun).

<sound> is the sound name of the template, and a sound that the template does not have gets
no event. `--event` adds an event or, with a text that the clip has, moves it (`+TEXT` adds
one more event with a text that the clip has; `{sound}` in a text is the sound name of the
template). `--no-events` writes a clip with only the events of `--event`. `--annotations`
gives the events of a vanilla clip to a clip of the synth step.

`--auto VANILLA.hkx` makes an automatic fire clip from the poses of one shot: the clip has
the length and the events of the vanilla automatic clip, and at each of its events weaponFire
the shot starts again from its first frame.

`--hold-end FRAMES` adds the last pose FRAMES times at the end of the clip. A graph of the
game can have a trigger at a time before the end of a clip: the put-away state of the
first-person weapon graph (GunBehavior, state WPNUnEquip) removes the gun 0.233 s before the
end of its clip. A source clip that is shorter than that time needs frames at its end.
"""
import argparse
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fo4clip  # noqa: E402  (adds fnv/tools to the path)
import port_hkx  # noqa: E402
import anim_fo4  # noqa: E402
from d2template import Template  # noqa: E402

FPS = 30

# The rotations of a clip. The spline clips of Fallout 4 have 48-bit rotations (format 2 in
# each vanilla clip of the pistol, revolver and submachine gun folders). The writer of
# fnv/tools asks its own function for 40-bit rotations (format 1), which have steps of
# 0.04 degrees: over the seven bones from the collarbone to the weapon that is a noise of
# 0.03 to 0.09 units at the muzzle from frame to frame, more than the motion of an idle clip.
# The function can write the two formats, so this program gives it the format of the game.
ROTATION_FORMAT = {48: 2, 40: 1}
_compress_all_blocks = anim_fo4._compress_all_blocks


def rotation_bits(bits):
    anim_fo4._compress_all_blocks = lambda anim, rot_quant=None: _compress_all_blocks(anim, rot_quant=ROTATION_FORMAT[bits])


def relative(poses, idx, bone, parent):
    """The matrix of a bone in the space of another bone, for each frame."""
    return np.linalg.inv(poses[:, idx[parent]]) @ poses[:, idx[bone]]


def away(rel, distance, degrees):
    """The frames where a relative matrix is not that of the last frame."""
    move = np.linalg.norm(rel[:, :3, 3] - rel[-1, :3, 3], axis=1)
    cos = (np.einsum('fij,ij->f', rel[:, :3, :3], rel[-1, :3, :3]) - 1.0) / 2.0
    turn = np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))
    return [int(f) for f in np.nonzero((move > distance) | (turn > degrees))[0]]


def reload_events(poses, names, template):
    idx = {n: i for i, n in enumerate(names)}
    roles = template.roles
    sounds = template.data.get('reload_sounds', [])
    prefix = template.data.get('reload_sound', template.sound)
    count = poses.shape[0]
    events = []

    def sound(name, frame):
        if name in sounds:
            events.append([frame, 'SoundPlay.%sReload%s' % (prefix, name)])
    last_part = 0
    if 'magazine' in roles:
        # a gun with a magazine: the magazine goes out and in, then the bolt (or the charging handle) moves
        magazine = away(relative(poses, idx, roles['magazine'], 'Weapon'), 0.3, 3.0)
        bolt = away(relative(poses, idx, roles['bolt'], 'Weapon'), 0.1, 2.0) if 'bolt' in roles else []
        if magazine:
            sound('MagOut', magazine[0])
            sound('MagIn', magazine[-1])
            last_part = magazine[-1]
        if bolt:
            sound('BoltOpen', bolt[0])
            sound('BoltClose', bolt[-1])
            last_part = max(last_part, bolt[-1])
        complete = magazine[-1] + 2 if magazine else count // 2
        events.append([complete, 'reloadComplete'])
    else:
        crane = away(relative(poses, idx, roles['crane'], 'Weapon'), 0.1, 2.0) if 'crane' in roles else []
        rounds = away(relative(poses, idx, roles['rounds'], roles['cylinder']), 0.3, 400.0) if 'rounds' in roles and 'cylinder' in roles else []
        if crane:
            sound('BoltOpen', crane[0])
            sound('BoltClose', crane[-1])
            last_part = crane[-1]
        if rounds:
            sound('MagIn', rounds[-1])
            last_part = max(last_part, rounds[-1])
        complete = last_part + 2 if (crane or rounds) else count // 2
        events.append([complete, 'reloadComplete'])
        hammer = [f for f in (away(relative(poses, idx, roles['hammer'], 'Weapon'), 0.1, 5.0) if 'hammer' in roles else []) if f > complete]
        if hammer:
            sound('Charge', hammer[0])
            last_part = max(last_part, hammer[-1])
    # the reload ends when the left hand is near its place of the last frame, and stays there
    end = count - 3
    far = away(relative(poses, idx, 'LArm_Hand', 'Weapon'), 6.0, 400.0)
    if far:
        end = min(end, far[-1] + 1)
    end = max(end, complete + 1, last_part + 2)
    end = min(end, count - 2)
    events += [[end - 1, 'initiateStart'], [end, 'reloadEnd']]
    return sorted(events, key=lambda e: e[0])


def clip_events(name, poses, names, template):
    if name.lower().startswith('wpnreload'):
        return reload_events(poses, names, template)
    if name.lower().startswith('wpnfire'):
        return [[0, 'weaponFire']]
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--poses', required=True)
    ap.add_argument('--name', required=True, help='the name of the Fallout 4 clip, for example WPNReload')
    ap.add_argument('--out', required=True)
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--event', action='append', default=[], help='FRAME=TEXT')
    ap.add_argument('--no-events', action='store_true')
    ap.add_argument('--rotation-bits', type=int, choices=(48, 40), default=48,
                    help='48: the rotation format of the vanilla clips; 40: the format that fnv/tools writes')
    ap.add_argument('--annotations', help='a file with the events of the clip ({"annotations": [[seconds, text], ...]}), '
                                         'in place of the events that the program finds')
    ap.add_argument('--camera-control', help='a vanilla clip (.hkx): the bone Camera Control has its place of the first '
                                             'frame of that clip on each frame')
    ap.add_argument('--hold-end', type=int, default=0, help='the last pose on this count of more frames at the end')
    ap.add_argument('--auto', help='a vanilla automatic fire clip (.hkx): the clip has its length, the first frames of '
                                   'the poses (one shot) from each of its events weaponFire, and its events')
    a = ap.parse_args()
    d = np.load(a.poses)
    poses = d['poses']
    names = [str(x) for x in d['names']]
    parents = [int(x) for x in d['parents']]
    fps = int(round(float(d['fps'])))
    if fps != FPS:
        raise SystemExit('%s: %d frames for each second; a Fallout 4 clip has %d' % (a.poses, fps, FPS))
    template = Template(a.template)
    if a.hold_end > 0:
        poses = np.concatenate([poses, np.repeat(poses[-1:], a.hold_end, axis=0)], axis=0)
    auto_events = None
    if a.auto:
        # Automatic fire from the clip of one shot: at each shot time of the vanilla clip the shot
        # starts again (fnv/tools/port_clips.py has the same rule).
        vanilla = anim_fo4.load_fo4_animation(a.auto)
        shots = sorted(int(round(x.time * FPS)) for x in vanilla.annotations if x.text == 'weaponFire')
        if not shots:
            raise SystemExit('%s has no event weaponFire' % a.auto)
        frames = [0] * shots[0]
        for k, start in enumerate(shots):
            end = shots[k + 1] if k + 1 < len(shots) else vanilla.num_frames
            frames += [min(i, poses.shape[0] - 1) for i in range(end - start)]
        poses = poses[frames]
        auto_events = [[int(round(x.time * FPS)), x.text] for x in vanilla.annotations]
    if a.camera_control:
        # The vanilla clips move this bone in the sights and in the sprint (see the template).
        skel = fo4clip.skeleton()
        _, vanilla, _, _ = fo4clip.decode(a.camera_control, skel)
        k = names.index('Camera Control')
        poses = np.array(poses, copy=True)
        poses[:, k] = vanilla[0, list(skel.bones).index('Camera Control')]
    events = [] if a.no_events else clip_events(a.name, poses, names, template)
    if a.annotations:
        events = [[int(round(t * FPS)), text] for t, text in json.load(open(a.annotations))['annotations']]
    if auto_events is not None:
        events = auto_events
    for text in a.event:
        frame, _, what = text.partition('=')
        what = what.replace('{sound}', template.sound)
        if what.startswith('+'):
            events = events + [[int(frame), what[1:]]]              # one more event with a text that the clip has
        else:
            events = [e for e in events if e[1] != what] + [[int(frame), what]]
    events.sort(key=lambda e: e[0])
    annotations = [(round(frame / FPS, 4), text) for frame, text in events]
    rotation_bits(a.rotation_bits)
    tr, ro, sc = port_hkx.local_tracks(poses, parents)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, a.name + '.hkx')
    port_hkx.write_clip(path, names, tr, ro, sc, fps, annotations)
    report = port_hkx.check_clip(path, tr, ro, sc, parents)
    report['events'] = events
    report['source'] = os.path.basename(a.poses)
    with open(os.path.join(a.out, a.name + '.json'), 'w') as f:
        json.dump(report, f, indent=1)
    print('[hkx] %-20s frames %4d  %.3f s  pos err %.4f  rot err %.3f deg  events %d' % (
        a.name, poses.shape[0], (poses.shape[0] - 1) / fps, report.get('max_world_position_error', -1),
        report.get('max_local_rotation_error_deg', -1), len(events)))
    for frame, text in events:
        print('[hkx]     %4d  %.4f s  %s' % (frame, frame / FPS, text))


if __name__ == '__main__':
    main()
