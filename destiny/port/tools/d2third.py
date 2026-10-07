#!/usr/bin/env python3
"""The third-person clips of a Destiny 2 weapon: the body of the player with the gun in its hand.

    ./port destiny third data/destiny/port/extract/NAME/manifest.json \
        [--state reload ...] [--stance stand] [-o data/destiny/port/extract/NAME/third_person]
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python \
        destiny/port/tools/d2third.py ...          (the same program with no ./port)

The extraction of a gun has its first-person rig, and the clips of the gun parts (`weapon_clips`
of the manifest). The third-person clips of the body are not in it: they are clips of the
player body entity (72 bones), which has one animation set (1467 clips) and one graph (332
states). The program reads them with the modules of destiny/extract/d2x (it does not change
them; the clip decoder is tiger-animation-parser, as for the first-person clips), so it runs
with the Python environment of d2x.

The graph (the layout is in d2x/graph.py). A state has a tree of conditions, and two of its
dimensions are known:

    3   the weapon tags, from `rifle`, `pistol` and `rocket_launcher` down to one weapon
    1   the stance: `stand` or `crouch` (FNV-1 hashes of these words)

A leaf of the tree is a clip. For a weapon the program takes, in each state, the leaf whose
last weapon tag is the first one in the tag list of the weapon that a leaf has. The list is
that of the first-person clips (d2x/graph.py, weapon_tags, with the tag tree of the
first-person rig): the content group of the weapon, the tags above it, the base type of its
class, the class, then `rifle`. The weapon type of `pattern` in the manifest comes after the
content group when the tag tree does not have it. For The Last Word that is the_last_word,
hand_cannon, revolver, pistol, rifle: its reload is the leaf of `pistol`. A leaf with the
stance 811C9DC5 (the hash of an empty word) is for each stance.

Some state names are known words. `reload` here is the state EB22859A (the hash of
`reload_1`). A shotgun that takes one shell at a time has three states in place of it:
`reload_enter`, 6C41757C (one shell; `--state 6C41757C=reload_loop` gives the file a name) and
`chamber_1`.

The clip of the gun parts of a state is from the graph of the gun entity: the state there
with the same name hash, and in it the leaf for this weapon. A state that the graph of the
gun does not have gets the gun with its parts at rest.

An additive clip has offsets only: the game adds them to the pose that the body has at that
time. The three clips of the reload of a shotgun are additive: the first one starts with no
offset, and the last one ends with no offset. The program adds the offsets to one pose,
`--base STATE[:FRAME]` (default: the first frame of the clip of `reload` in the leaf `rifle`,
which is the hold pose of each rifle), with the rule of d2x/anim.py: rotation = base x offset,
translation = base + offset, for each control of the rig. The program finds an additive clip
with the test of d2x/anim.py, or when each control has no offset in the first or in the last
frame; `--additive STATE` says it for a state.

Output, in the folder of -o:

    states.json          each state of the graph that has a leaf for this weapon: the tags of the
                         leaf, the clip, its frames
    STATE.npz            for each state of --state: the world matrix of each bone for each frame
                         (frames x bones x 4 x 4, column vectors), in the axes and the units of a
                         file of d2x (+Y up, +Z forward, +X to the left, meters), with
                         `names`, `parents` and `fps`, as tools/d2bake.py writes them. The bones
                         are the 72 bones of the body and the bones of the gun. The gun is on the
                         bone b_r_grip (in the first-person rig the gun bone has no offset from
                         it), and its bones have the motion of the gun clip of the state, when
                         the graph of the gun has that state.
    raw/                 the tags that the decoder reads (a skeleton, a rig, the clips)
"""
import argparse
import json
import os
import struct
import sys

import numpy as np

from d2x import pkg, entity as ent, graph as gr, anim, names as bone_names
from d2x.tag import Reader, fnv1

RIG = (0x80808F96, 0x80808F8F)
WEAPON_DIMENSION, STANCE_DIMENSION = 3, 1
STANCES = {fnv1('stand'): 'stand', fnv1('crouch'): 'crouch'}
ANY = fnv1('')                                              # a condition value for each stance
# names of states that are not in the word list of d2x/graph.py
STATES = {fnv1(w): w for w in ('reload_enter', 'chamber_1', 'sprint_ready', 'finisher_melee')}
STATES[fnv1('reload_1')] = 'reload'
WORDS = {fnv1(w): w for w in gr.STATE_WORDS + gr.TAG_WORDS}


def word(value):
    return STATES.get(value) or WORDS.get(value) or STANCES.get(value) or '%08X' % value


def quat_matrix(q):
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    m = np.empty(q.shape[:-1] + (3, 3))
    m[..., 0, 0] = 1 - 2 * (y * y + z * z)
    m[..., 0, 1] = 2 * (x * y - z * w)
    m[..., 0, 2] = 2 * (x * z + y * w)
    m[..., 1, 0] = 2 * (x * y + z * w)
    m[..., 1, 1] = 1 - 2 * (x * x + z * z)
    m[..., 1, 2] = 2 * (y * z - x * w)
    m[..., 2, 0] = 2 * (x * z - y * w)
    m[..., 2, 1] = 2 * (y * z + x * w)
    m[..., 2, 2] = 1 - 2 * (x * x + y * y)
    return m


def quat_multiply(a, b):
    """The product a x b of (x, y, z, w) rotations; `b` can have many rows."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], axis=-1)


class Body:
    """An entity with a skeleton, a rig and clips: the tags go into `raw` for the decoder."""

    def __init__(self, pm, tag, raw):
        self.pm, self.raw = pm, raw
        self.entity = ent.read_entity(pm, tag)
        skeleton, rig = self.entity.first(ent.SKELETON), self.entity.first(RIG)
        if skeleton is None or rig is None:
            raise SystemExit('the entity %08X has no skeleton or no rig' % tag)
        self.skeleton = ent.read_skeleton(skeleton)
        self.names = [bone_names.bone_name(h) for h in self.skeleton.hashes]
        self.parents = list(self.skeleton.parents)
        self.rig = anim.Rig(self.dump(skeleton.tag), self.dump(rig.tag), pm.version)

    def dump(self, tag):
        path = os.path.join(self.raw, '%08X.bin' % tag)
        if not os.path.isfile(path):
            with open(path, 'wb') as f:
                f.write(self.pm.read(tag))
        return path

    def additive(self, clip_tag):
        """True for a clip with offsets only: the test of d2x/anim.py, or no offset of each control in
        the first or in the last frame."""
        _, tracks = self.rig.controls(self.dump(clip_tag))
        if self.rig.is_additive(tracks):
            return True
        for frame in (0, -1):
            zero = True
            for track in tracks:
                if track.translations is not None and np.abs(np.asarray(track.translations, float).reshape(-1, np.asarray(track.translations).shape[-1])[frame, :3]).max() > 1e-3:
                    zero = False
                if track.rotations is not None and abs(np.asarray(track.rotations, float).reshape(-1, 4)[frame, 3]) < 0.9999:
                    zero = False
            if zero:
                return True
        return False

    def local(self, clip_tag, base=None):
        """The local matrix of each bone for each frame of a clip: frames x bones x 4 x 4.
        `base`: (clip tag, frame), the pose below a clip that has offsets only."""
        data, tracks = self.rig.controls(self.dump(clip_tag))
        if base is not None:
            # the rule of d2x/anim.py (Rig.decode), with one frame of the base clip
            _, under = self.rig.controls(self.dump(base[0]))
            for track, reference in zip(tracks, under):
                if reference.rotations is not None:
                    rows = np.asarray(reference.rotations, float).reshape(-1, 4)
                    first = rows[min(base[1], len(rows) - 1)]
                    track.rotations = (first[None] if track.rotations is None
                                       else quat_multiply(first, np.asarray(track.rotations, float))).astype(np.float32)
                if reference.translations is not None:
                    rows = np.asarray(reference.translations, float)
                    rows = rows.reshape(-1, rows.shape[-1])[:, :3]
                    first = rows[min(base[1], len(rows) - 1)]
                    track.translations = (first[None] if track.translations is None
                                          else np.asarray(track.translations, float)[..., :3] + first).astype(np.float32)
                if reference.scales is not None:
                    rows = np.asarray(reference.scales, float).reshape(-1)
                    first = float(rows[min(base[1], len(rows) - 1)])
                    track.scales = (np.array([first]) if track.scales is None else np.asarray(track.scales, float) * first).astype(np.float32)
        solved = anim.convert_obj_to_local(data, anim.rig_retarget(data, tracks, self.rig.skeleton, self.rig.rig), self.rig.skeleton)
        rotations = np.moveaxis(np.stack([np.asarray(t.rotations, float) for t in solved]), 0, 1)       # frames x bones x 4
        translations = np.moveaxis(np.stack([np.asarray(t.translations, float) for t in solved]), 0, 1)
        scales = np.moveaxis(np.stack([np.asarray(t.scales, float) for t in solved]), 0, 1)
        if scales.ndim == 2:
            scales = np.repeat(scales[..., None], 3, axis=-1)
        frames, bones = rotations.shape[:2]
        out = np.zeros((frames, bones, 4, 4))
        out[..., :3, :3] = quat_matrix(rotations) * scales[..., None, :]
        out[..., :3, 3] = translations[..., :3]
        out[..., 3, 3] = 1.0
        return out

    def sets(self):
        for resource in self.entity.by_kind(ent.ANIMATION):
            for set_tag in ent.animation_sets(self.pm, resource):
                yield resource, set_tag


def world_of(local, parents):
    world = np.zeros_like(local)
    done = set()

    def solve(i):
        if i in done:
            return
        p = parents[i]
        if p >= 0:
            solve(p)
            world[:, i] = world[:, p] @ local[:, i]
        else:
            world[:, i] = local[:, i]
        done.add(i)
    for i in range(local.shape[1]):
        solve(i)
    return world


def leaves(pm, graph_tag):
    """Each leaf of each state of a graph: (state index, name hashes, conditions, clip entries)."""
    data = pm.read(graph_tag)
    r = Reader(data)
    name_count, names_at, _ = r.array(0x08)
    state_count, states_at, _ = r.array(0x18)
    names = {}
    for i in range(name_count):
        names.setdefault(r.u32(names_at + i * 8 + 4), []).append(r.u32(names_at + i * 8))
    out = []
    for index in range(state_count):
        kind = r.u64(states_at + index * 16)
        base = r.rel(states_at + index * 16 + 8)
        if kind == 1:
            out.append((index, names.get(index, []), [], gr._clip_list(r, base)))
            continue
        entries = [gr._clip_list(r, o) for o in r.array_items(base, 16)]
        node_count, nodes_at, _ = r.array(base + 0x20)
        group_count, groups_at, _ = r.array(base + 0x30)
        groups = [(r.u16(groups_at + i * 4), r.u16(groups_at + i * 4 + 2)) for i in range(group_count)]

        def node(i):
            o = nodes_at + i * 0x1C
            return r.u32(o + 16), r.i16(o + 20), r.i16(o + 22), r.i16(o + 24)

        def walk(group, conditions, depth):
            if not 0 <= group < len(groups) or depth > 16:
                return
            dimension, first = groups[group]

            def level(i, conditions):
                seen = set()
                while 0 <= i < node_count and i not in seen:
                    seen.add(i)
                    value, child, sibling, link = node(i)
                    here = conditions + [(dimension, value)]
                    if link > 0:
                        walk(link - 1, here, depth + 1)
                    elif link < 0 and -link - 1 < len(entries):
                        out.append((index, names.get(index, []), here, entries[-link - 1]))
                    if child >= 0:
                        level(child, here)             # a tag below this tag, in the same dimension
                    i = sibling
            level(first, conditions)
        walk(0, [], 0)
    return out


def first_clip(clip_list, entries, clips):
    """The clip tag of the first entry of a leaf, or None."""
    for entry, _ in clip_list:
        if entry < len(entries) and entries[entry][2] < len(clips):
            return clips[entries[entry][2]]
    return None


def gun_states(pm, gun, tags):
    """The clip of the gun parts for each state of the graph of the gun entity: name hash -> clip tag."""
    out = {}
    for resource in gun.entity.by_kind(ent.ANIMATION):
        graph = gr.find_graph(pm, resource.data)
        sets = list(ent.animation_sets(pm, resource))
        if not graph or not sets:
            continue
        clips = ent.animation_set_clips(pm, sets[0])
        entries = gr.read_set_entries(pm.read(sets[0]))
        best = {}
        for index, names, conditions, clip_list in leaves(pm, graph):
            weapon = [v for d, v in conditions if d == WEAPON_DIMENSION]
            if weapon and weapon[-1] not in tags:
                continue
            rank = tags.index(weapon[-1]) if weapon else len(tags)
            tag = first_clip(clip_list, entries, clips)
            if tag is not None and pm.exists(tag) and (index not in best or rank < best[index][0]):
                best[index] = (rank, names, tag)
        for _, names, tag in best.values():
            for name in names:
                out.setdefault(name, tag)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest', help='manifest.json of the extraction of the weapon')
    ap.add_argument('--state', action='append', default=[],
                    help='a state to bake (default: reload): its name or its hash; STATE=NAME gives the file the name NAME')
    ap.add_argument('--stance', default='stand')
    ap.add_argument('--base', default='reload', help='STATE[:FRAME]: the pose below a clip that has offsets only '
                                                     '(default: the first frame of `reload` in the leaf `rifle`)')
    ap.add_argument('--additive', action='append', default=[], help='a state of --state whose clip has offsets only')
    ap.add_argument('-o', '--output')
    a = ap.parse_args()
    manifest = json.load(open(a.manifest))
    out = a.output or os.path.join(os.path.dirname(os.path.abspath(a.manifest)), 'third_person')
    raw = os.path.join(out, 'raw')
    os.makedirs(raw, exist_ok=True)
    pm = pkg.PackageManager()
    body = Body(pm, int(manifest['first_person'][0]['body'][0]['entity'], 16), raw)
    gun = Body(pm, int(manifest['pattern']['entity'], 16), raw)
    tags = [int(manifest['pattern']['content_group'], 16)]
    # the tag list of the weapon, from the tag tree of its first-person rig
    first_person = ent.read_entity(pm, int(manifest['first_person'][0]['entity'], 16))
    for resource in first_person.by_kind(ent.ANIMATION):
        tree = gr.find_tag_tree(pm, resource.data)
        if tree:
            for tag in gr.weapon_tags(gr.read_tag_tree(pm.read(tree)), tags[0]):
                if tag not in tags:
                    tags.append(tag)
            break
    weapon_type = int(manifest['pattern']['weapon_type'], 16) if manifest['pattern'].get('weapon_type') else None
    if weapon_type is not None and weapon_type not in tags:
        tags.insert(1, weapon_type)
    # the tags of this weapon and of its type
    own_tags = tags.index(weapon_type) + 1 if weapon_type is not None else 1
    if fnv1('rifle') not in tags:
        tags.append(fnv1('rifle'))
    resource, set_tag = next(body.sets())
    clips = ent.animation_set_clips(pm, set_tag)
    entries = gr.read_set_entries(pm.read(set_tag))
    graph_tag = gr.find_graph(pm, resource.data)

    # the leaf of each state for this weapon and this stance
    chosen = {}
    rifle = {}                                              # state index -> the clip of its leaf `rifle`
    for index, names, conditions, clip_list in leaves(pm, graph_tag):
        weapon = [v for d, v in conditions if d == WEAPON_DIMENSION]
        stance = [a.stance if v == ANY else STANCES.get(v, '%08X' % v) for d, v in conditions if d == STANCE_DIMENSION]
        if stance and a.stance not in stance:
            continue
        if weapon == [fnv1('rifle')] and all(d in (WEAPON_DIMENSION, STANCE_DIMENSION) for d, _ in conditions):
            rifle.setdefault(index, (names, first_clip(clip_list, entries, clips)))
        if not weapon:
            continue
        if weapon[-1] not in tags:
            continue
        rank = tags.index(weapon[-1])
        other = tuple((d, v) for d, v in conditions if d not in (WEAPON_DIMENSION, STANCE_DIMENSION))
        key = (index, other)
        if key not in chosen or rank < chosen[key][0]:
            chosen[key] = (rank, names, conditions, clip_list)
    states = []
    for (index, other), (rank, names, conditions, clip_list) in sorted(chosen.items()):
        rows = []
        for entry, weight in clip_list:
            if entry < len(entries) and entries[entry][2] < len(clips):
                tag = clips[entries[entry][2]]
                rows.append({'clip': '%08X' % tag, 'frames': anim.clip_header(pm.read(tag))['frames'], 'weight': weight})
        states.append({'state': index, 'names': [word(h) for h in names], 'hashes': ['%08X' % h for h in names],
                       'tags': [word(v) for d, v in conditions if d == WEAPON_DIMENSION],
                       'own': rank < own_tags, 'conditions': ['%d:%s' % (d, word(v)) for d, v in other], 'clips': rows})
    with open(os.path.join(out, 'states.json'), 'w') as f:
        json.dump({'item': manifest['name'], 'body': '%08X' % body.entity.tag, 'set': '%08X' % set_tag, 'graph': '%08X' % graph_tag,
                   'stance': a.stance, 'tags': [word(t) for t in tags], 'states': states}, f, indent=1)
    own = [s for s in states if s['own']]
    print('[third] %s: the tags %s' % (manifest['name'], ', '.join(word(t) for t in tags)))
    print('[third] %s: %d states have a leaf for the weapon, %d of them with a tag of this weapon: %s' % (
        manifest['name'], len(states), len(own), ', '.join('%s (%s, %d frames)' % ('/'.join(s['names']), s['clips'][0]['clip'], s['clips'][0]['frames'])
                                                           for s in own if s['clips'])))

    # the clips of the gun parts: the states of the graph of the gun entity
    gun_clips = gun_states(pm, gun, tags)
    grip = body.names.index('b_r_grip')
    for text in a.state or ['reload']:
        name, _, file_name = text.partition('=')
        found = [s for s in states if (name in s['names'] or name.upper() in s['hashes']) and not s['conditions'] and s['clips']]
        if not found:
            raise SystemExit('the graph has no state %s for this weapon' % name)
        tag = int(found[0]['clips'][0]['clip'], 16)
        under = None
        if name in a.additive or body.additive(tag):
            # the pose below the offsets: one frame of the clip of the base state in the leaf `rifle`
            state, _, frame = a.base.partition(':')
            below = [t for names, t in rifle.values() if t is not None and (state in [word(h) for h in names] or state.upper() in ['%08X' % h for h in names])]
            if not below:
                raise SystemExit('the graph has no state %s in the leaf rifle (the base of an additive clip)' % state)
            under = (below[0], int(frame or 0))
        name = file_name or name
        local = body.local(tag, under)
        world = world_of(local, body.parents)
        frames = world.shape[0]
        near = [gun_clips[int(h, 16)] for h in found[0]['hashes'] if int(h, 16) in gun_clips]
        gun_local = None
        note = 'the graph of the gun does not have this state: the gun parts do not move'
        if near:
            gun_local = gun.local(near[0])
            note = 'the gun parts have the clip %08X (%d frames)' % (near[0], gun_local.shape[0])
            if gun_local.shape[0] < frames:                 # the last pose on the frames that the clip does not have
                gun_local = np.concatenate([gun_local, np.repeat(gun_local[-1:], frames - gun_local.shape[0], axis=0)])
            gun_local = gun_local[:frames]
        else:
            rest = np.zeros((len(gun.names), 4, 4))
            rest[:, 3, 3] = 1.0
            rest[:, :3, :3] = quat_matrix(gun.skeleton.rotations[:, [1, 2, 0, 3]]) * gun.skeleton.scales[:, None, None]
            rest[:, :3, 3] = gun.skeleton.translations[:, [1, 2, 0]]
            local_rest = rest.copy()
            for i, p in enumerate(gun.parents):
                if p >= 0:
                    local_rest[i] = np.linalg.inv(rest[p]) @ rest[i]
            gun_local = np.repeat(local_rest[None], frames, axis=0)
        gun_world = world_of(gun_local, gun.parents)
        # The rest place of the root of the gun is on the grip bone. A clip of the gun can move the
        # root against that place (the revolver turns in the hand in its reload).
        root = gun.parents.index(-1)
        root_rest = np.eye(4)
        root_rest[:3, :3] = quat_matrix(gun.skeleton.rotations[root][[1, 2, 0, 3]]) * gun.skeleton.scales[root]
        root_rest[:3, 3] = gun.skeleton.translations[root][[1, 2, 0]]
        gun_world = world[:, grip][:, None] @ (np.linalg.inv(root_rest) @ gun_world)
        names = body.names + gun.names
        parents = body.parents + [grip if p < 0 else p + len(body.names) for p in gun.parents]
        np.savez_compressed(os.path.join(out, name + '.npz'), world=np.concatenate([world, gun_world], axis=1),
                            names=np.array(names), parents=np.array(parents), fps=anim.FRAME_RATE)
        if under:
            note += '; the clip has offsets only, on frame %d of the clip %08X' % (under[1], under[0])
        print('[third] %s: the clip %08X (the leaf %s), %d frames, %d bones of the body and %d bones of the gun; %s' % (
            name, tag, '/'.join(found[0]['tags']), frames, len(body.names), len(gun.names), note))


if __name__ == '__main__':
    main()
