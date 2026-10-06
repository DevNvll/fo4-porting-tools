"""The clip table of a weapon port: which source gives each Fallout 4 clip.

The table is in the configuration file of the weapon ([clips.NAME] in port.toml):

    source = "SCENE"                  the whole pose file SCENE.npz
    parts = [["SCENE", 0, 20], ...]   or: a list of (pose file, first frame, last frame); -1 is the end
    events = [[14, "TEXT"], ...]      annotations: the frame (30 for each second) and the text
    hold = 30                         the first pose of the source on 30 frames (a source with one pose)
    auto = ["A", "B", "C"]            automatic fire: the first frames of these single shot clips at the
                                      shot times of the vanilla clip of the template
    synth = true                      a clip of tools/blender/synth.py (the pose file synth_NAME.npz)

In an event text, {sound} is the sound name of the template weapon.
"""
import json
import os
import numpy as np

import port_config as cfg

FPS = cfg.FPS


def f(frame):
    return round(frame / FPS, 4)


def auto(variants):
    shot_frames = list(cfg.TEMPLATE['auto']['shot_frames'])
    parts = []
    shots = shot_frames + [cfg.TEMPLATE['auto']['frames']]
    for k in range(len(shot_frames)):
        n = shots[k + 1] - shots[k]
        parts.append((variants[k % len(variants)], 0, n - 1))
    return {'parts': parts, 'annotations': [(f(x), 'weaponFire') for x in shot_frames],
            'note': 'automatic fire: the first frames of the single shot clips at the shot times of the vanilla clip'}


def clips():
    t = {}
    for name, c in cfg.D.get('clips', {}).items():
        if c.get('synth'):
            t[name] = {'parts': [('synth_' + name, 0, None)], 'synth': True,
                       'note': 'the weapon motion of the vanilla clip %s on the pose of the gun' % name}
            continue
        if 'auto' in c:
            t[name] = auto(list(c['auto']))
            continue
        if 'parts' in c:
            parts = [(s, int(a), None if int(b) < 0 else int(b)) for s, a, b in c['parts']]
        else:
            parts = [(c['source'], 0, None)]
        clip = {'parts': parts}
        if 'hold' in c:
            clip['hold'] = int(c['hold'])
        if 'events' in c:
            clip['annotations'] = [(f(frame), text.replace('{sound}', cfg.SOUND)) for frame, text in c['events']]
        t[name] = clip
    return t


def build(clip, src):
    chunks = []
    names = parents = fps = None
    for scene, a, b in clip['parts']:
        poses, names, parents, fps = src.get(scene)
        b = poses.shape[0] - 1 if b is None else min(b, poses.shape[0] - 1)
        chunks.append(poses[a:b + 1])
    ann = list(clip.get('annotations', []))
    if clip.get('synth'):
        meta = json.load(open(os.path.join(src.folder, clip['parts'][0][0] + '.json')))
        ann = [(float(t), text) for t, text in meta['annotations']]
    poses = np.concatenate(chunks, axis=0)
    if clip.get('hold'):
        # a pose of the source (a clip with one pose) on this count of frames
        poses = np.repeat(poses[:1], clip['hold'], axis=0)
    return poses, names, parents, fps, ann
