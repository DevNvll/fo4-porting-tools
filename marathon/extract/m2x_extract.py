#!/usr/bin/env python3
"""Extract a weapon of Marathon: the models, the textures, the skeletons and the clips, as glTF files.

    ./port marathon find TEXT
    ./port marathon extract ITEM [--art ITEM] [--out OUT] [--arms NUMBER] [--hands FILE.glb] [--all-detail] [--stages 0,2]

The same with no `./port` (the Python of the environment of d2x, from the root of the repository):

    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/m2x_extract.py ITEM ...

ITEM is the name or the hash (hexadecimal) of an item. `--find TEXT` prints the items whose
name has TEXT. An item with no row in the art table of the game (a variant of another weapon)
needs `--art`: the item whose entity it uses.

The program does not change d2x (destiny/extract/d2x): it uses its modules for the package
access, the glTF writer and the animation decoder (tiger-animation-parser), and m2x.py for
the layouts of Marathon. Output, in OUT/NAME/ (default OUT: data/marathon/extract/out):

    NAME_weapon.glb         the skeleton of the weapon, the pieces, and one animation for each clip of the weapon
    NAME_first_person.glb   the first-person rig (the body skeleton with the bones of the weapon on the
                            right hand), the pieces, and one animation for each clip that the animation
                            graph has for this weapon. It has the form of a first-person file of
                            d2x, so the tools of destiny/port read it.
    NAME_PIECE.glb          each piece alone, in its own space, on its own skeleton
    textures/TAG.png        each texture of each material of the pieces
    textures/MATERIAL_albedo.png, _normal.png, _gstack.png
                            each material as a texture set of Destiny 2 (m2x.material_plates)
    manifest.json           the item, the entities, the pieces, the materials, the clips, the first-person rig
    states.json             the clip of each game state (the form of destiny/port/tools/d2states.py)
    raw/TAG.bin             the tags that the animation decoder reads

**The pieces.** A weapon of Marathon is a set of pieces: each piece is an entity with a model,
and the weapon has a slot for each one (barrel, sight, magazine, ...). The weapon entity has
named points, each on a bone of its skeleton. A piece names one of them, and its own point
`attachment` goes there (m2x.markers, m2x.attach_point). A piece with no such name and no slot
has the coordinates of the weapon (the body). An entity below a piece (the second magazine of
the reload) has no place, and it is only in its own file.

**The first-person rig.** The slots component of the weapon names a list of arm entities, one
for each body of the player (`--arms NUMBER` selects one; default: the first one, which has no
body name). An arm entity has the skeleton, the rig, an animation set and an animation graph.
The graph gives the clips of each game state for the tags of the weapon (m2x.read_graph). The
file has each such clip (fp_NNN_TAG: NNN is its place in the set) and each clip of the weapon
entity on the same skeleton (weapon_NNN_TAG: the body bones at rest, the gun parts as in the
clip). A clip of the arms does not move the gun parts in a reload: the clip of the weapon
with the same length has that motion, and the game plays the two at the same time.

`--hands FILE.glb` copies the mesh `body_hands` of a first-person file of Destiny 2 onto the
skeleton (the bones have the same names): the hands of another game, for pictures only.
"""
import argparse
import dataclasses
import json
import os
import re
import sys

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m2x  # noqa: E402  (it puts destiny/extract, the folder of d2x, on the path, and it stops when this Python is not that of d2x)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from d2x import anim, export, graph as gr  # noqa: E402

FRAME_RATE = 30.0
PATTERN_LIST = 0x808025AA          # the list of arm entities of a weapon (64-bit hashes), with their source names


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def word(value):
    """The word of a name hash: a state, a tag or a bone."""
    return gr.STATE_NAMES.get(value) or (m2x.name_of(value) if value != m2x.EMPTY else '')


def skeleton_data(tag, parsed):
    """export.SkeletonData from a skeleton of the animation parser (Tiger axes -> glTF axes)."""
    count = parsed.node_defs.length
    hashes = [int(n.bone_hash) & 0xFFFFFFFF for n in parsed.node_defs]
    parents = [int(n.parent_node_index) for n in parsed.node_defs]
    world = np.zeros((count, 4, 4))
    for i, t in enumerate(parsed.default_obj_space_tr):
        r, ts = np.array(t.r, float), np.array(t.ts, float)
        world[i, :3, :3] = export.quat_matrix(r[[1, 2, 0, 3]]) * ts[3]
        world[i, :3, 3] = ts[[1, 2, 0]]
        world[i, 3, 3] = 1
    local = world.copy()
    for i, parent in enumerate(parents):
        if parent >= 0:
            local[i] = np.linalg.inv(world[parent]) @ world[i]
    labels, used = [], {}
    for h in hashes:
        name = m2x.name_of(h, 'bone_')
        used[name] = used.get(name, -1) + 1
        labels.append(name if used[name] == 0 else '%s.%03d' % (name, used[name]))
    return export.SkeletonData(tag, hashes, labels, parents, world, local)


def bind_game(parsed):
    """The bind matrix of each bone of a skeleton of the animation parser, in the axes of the game."""
    out = []
    for t in parsed.default_obj_space_tr:
        r, ts = np.array(t.r, float), np.array(t.ts, float)
        m = np.eye(4)
        m[:3, :3] = export.quat_matrix(r) * ts[3]
        m[:3, 3] = ts[:3]
        out.append(m)
    return out


def find_item(inv, text):
    if re.fullmatch(r'[0-9A-Fa-f]{8}', text) and int(text, 16) in inv.display:
        return int(text, 16)
    found = inv.find(text)
    if not found:
        raise SystemExit('no item has the name %s' % text)
    exact = [h for h in found if inv.name(h).lower() == text.lower()]
    with_entity = [h for h in (exact or found) if inv.entity(h)]
    return (with_entity or exact or found)[0]


def moved(parts, matrix, bone):
    """The parts of a piece at their place in the weapon: on one bone, moved by `matrix` (the axes of the game)."""
    r, t = matrix[:3, :3].astype(np.float32), matrix[:3, 3].astype(np.float32)
    out = []
    for p in parts:
        tangents = p.tangents
        if tangents is not None:
            tangents = np.concatenate([tangents[:, :3] @ r.T, tangents[:, 3:4]], axis=1)
        out.append(dataclasses.replace(
            p, positions=p.positions @ r.T + t, normals=p.normals @ r.T if p.normals is not None else None, tangents=tangents,
            joints=np.full_like(p.joints, bone), weights=np.tile(np.array([[1, 0, 0, 0]], np.float32), (len(p.positions), 1))))
    return out


def arm_entities(pm, components, t64):
    """[(source name, entity tag)] of the arm entities of a weapon, in the order of its list."""
    import struct
    out = []
    for c in components:
        if c.kind != m2x.WEAPON_PARTS:
            continue
        for tag in m2x.tags_in(pm, c.data, PATTERN_LIST):
            data = pm.read(tag)
            names = [m.group().decode('latin1').rsplit('\\', 1)[-1].replace('.pattern.tft', '')
                     for m in re.finditer(rb'content\\[\x20-\x7e]+?\.pattern\.tft', data)]
            found = []
            for o in range(0, len(data) - 8, 8):
                row = t64.get(struct.unpack_from('<Q', data, o)[0])
                if row and row[1] == m2x.ENTITY:
                    found.append(row[0])
            out += [(names[i] if i < len(names) else '', e) for i, e in enumerate(found)]
    return out


def rest_clip(skeleton, name, frames):
    """A clip with each bone of a skeleton at its rest place."""
    count = len(skeleton)
    trs = [export.decompose(skeleton.local[i]) for i in range(count)]
    return anim.Clip(name, frames, 0, count, count, (-1, -1),
                     np.repeat(np.array([t[2] for t in trs], np.float32)[:, None], frames, axis=1),
                     np.repeat(np.array([t[1] for t in trs], np.float32)[:, None], frames, axis=1),
                     np.repeat(np.array([t[0] for t in trs], np.float32)[:, None], frames, axis=1),
                     np.zeros(count, bool))


def hands_of(path, skeleton):
    """The mesh `body_hands` of a first-person file of Destiny 2 as a mesh set for `skeleton`
    (each vertex on the bone with the same name), and a record for the manifest."""
    from d2x.model import Part
    from d2x.tag import fnv1
    sys.path.insert(0, paths.repo('destiny', 'port', 'tools'))      # the glTF reader of destiny/port
    from glb import Glb
    g = Glb(path)
    node = g.nodes[g.node_index('body_hands')]
    skin = g.json['skins'][node['skin']]
    names = [g.nodes[j]['name'] for j in skin['joints']]
    world = np.linalg.inv(g.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1))
    parents = [names.index(g.nodes[g.parent[j]]['name']) if g.parent.get(j) in skin['joints'] else -1 for j in skin['joints']]
    local = world.copy()
    for i, p in enumerate(parents):
        if p >= 0:
            local[i] = np.linalg.inv(world[p]) @ world[i]
    source = export.SkeletonData(0, [fnv1(n) for n in names], names, parents, world, local)
    parts = []
    for prim in g.json['meshes'][node['mesh']]['primitives']:
        a = prim['attributes']
        # the file has the axes of glTF, and a part has the axes of the game: [y, z, x] -> [x, y, z]
        back = [2, 0, 1]
        parts.append(Part(0, len(parts), 0, 1, 0xFFFFFFFF, g.accessor(a['POSITION'])[:, back].astype(np.float32),
                          g.accessor(a['NORMAL'])[:, back].astype(np.float32) if 'NORMAL' in a else None, None,
                          g.accessor(a['TEXCOORD_0']).astype(np.float32) if 'TEXCOORD_0' in a else None, None,
                          g.accessor(a['JOINTS_0']).astype(np.uint16), g.accessor(a['WEIGHTS_0']).astype(np.float32),
                          g.accessor(prim['indices']).reshape(-1, 3).astype(np.uint32)))
    missing = sorted({names[j] for p in parts for j in np.unique(p.joints[p.weights > 0]).tolist()} - set(skeleton.names))
    record = {'name': 'the hands of Destiny 2 (not a mesh of Marathon; for pictures only)', 'file': os.path.basename(path),
              'parts': len(parts), 'triangles': int(sum(len(p.triangles) for p in parts)), 'bones_not_in_the_rig': missing}
    return export.MeshSet('body_hands', parts, source, {}, 'destiny_hands'), record


def main():
    ap = argparse.ArgumentParser(description='Extract a weapon of Marathon as glTF files: the models, the textures, the skeletons and the clips.')
    ap.add_argument('item', nargs='?', help='the name or the hash (hexadecimal) of an item')
    ap.add_argument('--find', metavar='TEXT', nargs='?', const='', help='print the items whose name has TEXT (no TEXT: each item with a name), and stop')
    ap.add_argument('--art', help='the item whose entity this item uses')
    ap.add_argument('--out', default=m2x.OUT, help='the output folder; the files go into OUT/NAME (default: data/marathon/extract/out)')
    ap.add_argument('--arms', type=int, default=0, help='the number of the arm entity in the list of the weapon (default 0)')
    ap.add_argument('--hands', help='a first-person file of Destiny 2: its mesh `body_hands` goes on the first-person rig')
    ap.add_argument('--no-first-person', action='store_true')
    ap.add_argument('--all-detail', action='store_true', help='each detail level of each part (default: the highest)')
    ap.add_argument('--stages', default='0', help='the render stages of the parts (default: 0, the opaque parts)')
    a = ap.parse_args()
    if a.item is None and a.find is None:
        ap.error('give ITEM (the name or the hash of an item), or --find TEXT')
    pm = m2x.open_packages()
    t64 = m2x.tag64_table()
    inv = m2x.Investment(pm, t64)
    if a.find is not None:
        for h in inv.find(a.find):
            print('%08X  %-40s %s' % (h, inv.name(h), 'entity %08X' % inv.entity(h) if inv.entity(h) else 'no entity of its own'))
        return
    item = find_item(inv, a.item)
    title = inv.name(item)
    entity = inv.entity(item)
    art = item
    if not entity:
        if not a.art:
            raise SystemExit('the item %s (%08X) has no row in the art table. Give --art ITEM: the item whose entity it uses.' % (title, item))
        art = find_item(inv, a.art)
        entity = inv.entity(art)
        if not entity:
            raise SystemExit('the item %s (%08X) has no entity' % (inv.name(art), art))
    name = slug(title)
    root = os.path.join(a.out, name)
    for d in ('raw', 'textures'):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    print('[m2x] %s (%08X): entity %08X%s' % (title, item, entity, '' if art == item else ', from the item %s (%08X)' % (inv.name(art), art)))

    def dump(tag):
        path = os.path.join(root, 'raw', '%08X.bin' % tag)
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(pm.read(tag))
        return path

    m2x.patch_parser()
    manifest = {'game': 'Marathon', 'name': title, 'item': title, 'item_hash': '%08X' % item, 'art_item': inv.name(art),
                'art_item_hash': '%08X' % art, 'entity': '%08X' % entity, 'frame_rate': FRAME_RATE,
                'axes': 'glTF: +Y up, +Z forward (game: +Z up, +X forward)', 'files': {},
                'pieces': [], 'materials': {}, 'textures': {}, 'clips': []}

    # the skeleton and the rig of the weapon
    components = m2x.read_entity(pm, entity)
    skeleton_c = next((c for c in components if c.kind == m2x.SKELETON), None)
    rig_c = next((c for c in components if c.kind == m2x.RIG), None)
    if skeleton_c is None or rig_c is None:
        raise SystemExit('the entity %08X has no skeleton or no rig' % entity)
    rig = anim.Rig(dump(skeleton_c.tag), dump(rig_c.tag), 'marathon')
    skeleton = skeleton_data(skeleton_c.tag, rig.skeleton)
    bind = bind_game(rig.skeleton)
    manifest['weapon_skeleton'] = {'tag': '%08X' % skeleton_c.tag, 'rig': '%08X' % rig_c.tag, 'bones': skeleton.names,
                                   'parents': skeleton.parents}
    print('[m2x] skeleton %08X: %d bones: %s' % (skeleton_c.tag, len(skeleton), ', '.join(skeleton.names)))

    # the pieces: each entity below the weapon entity with a model
    stages = tuple(int(s) for s in a.stages.split(','))
    detail = None if a.all_detail else m2x.DETAIL_HIGH
    pieces, seen = [], set()

    def visit(tag, depth, path):
        if tag in seen or depth > 3:
            return
        seen.add(tag)
        own = m2x.read_entity(pm, tag)
        models = [(c, m) for c in own if c.kind == m2x.MODEL for m in m2x.tags_in(pm, c.data, m2x.MODEL_TAG)]
        if models and tag != entity:
            sk = next((c for c in own if c.kind == m2x.SKELETON), None)
            pieces.append((tag, path, models, sk, own))
        for child in m2x.child_entities(pm, tag, t64):
            visit(child, depth + 1, path + [tag])
    visit(entity, 0, [])

    textures = {}

    def texture_file(tag):
        if tag not in textures:
            pixels, info = m2x.read_texture(pm, tag)
            file = os.path.join('textures', '%08X.png' % tag)
            Image.fromarray(pixels).save(os.path.join(root, file))
            textures[tag] = (pixels, info, file)
            manifest['textures']['%08X' % tag] = {'file': file, 'width': info.width, 'height': info.height, 'format': info.dxgi_format,
                                                  'srgb': bool(info.srgb), 'mean': [round(float(x), 1) for x in pixels.reshape(-1, 4).mean(axis=0)]}
        return textures[tag]

    def plates_of(material):
        """The textures of a material in the form of Destiny 2 (m2x.material_plates): the plates of
        export.build_glb, and the files textures/MATERIAL_albedo.png, _normal.png and _gstack.png."""
        if material in plate_cache:
            return plate_cache[material]
        for slot, tag in m2x.material_textures(pm, material, t64):
            try:
                texture_file(tag)
            except Exception as error:
                print('[m2x]   texture %08X of the material %08X: %s' % (tag, material, error))
        plates, record = m2x.material_plates(pm, material, t64, lambda tag: texture_file(tag)[:2])
        for kind, pixels in plates.items():
            Image.fromarray(pixels).save(os.path.join(root, 'textures', '%08X_%s.png' % (material, kind)))
        manifest['materials']['%08X' % material] = record
        plate_cache[material] = plates
        return plates

    plate_cache = {}
    handle = export.SkeletonData(0, [skeleton.hashes[0]], [skeleton.names[0]], [-1], np.eye(4)[None], np.eye(4)[None])
    slots = m2x.weapon_slots(pm, components, t64)
    controls = m2x.rig_controls(rig_c)
    points = m2x.markers(components)
    manifest['slots'] = [{'slot': m2x.name_of(h), 'hash': '%08X' % h, 'entity': '%08X' % e if e else None,
                          'bone': skeleton.names[controls[h]] if h in controls else None} for h, e in slots]
    manifest['rig_controls'] = {m2x.name_of(h): skeleton.names[b] for h, b in controls.items() if b < len(skeleton)}
    manifest['points'] = {m2x.name_of(h): {'bone': skeleton.names[b] if b < len(skeleton) else b, 'rotation': [round(float(x), 5) for x in q],
                                           'translation': [round(float(x), 5) for x in t]} for h, (b, q, t, _) in points.items()}
    slot_of = {e: h for h, e in slots if e}
    # the body first, then the pieces of the slots
    pieces = [row for _, row in sorted(enumerate(pieces), key=lambda x: (x[1][0] in slot_of or len(x[1][1]) > 1, x[0]))]
    weapon_sets = []
    for tag, path, models, sk, own in pieces:
        piece_skeleton = None
        if sk is not None:
            try:
                from tag_readers.read_skeleton import read_skeleton
                from tag.game_version import Game_Version
                with open(dump(sk.tag), 'rb') as f:
                    piece_skeleton = skeleton_data(sk.tag, read_skeleton(f, Game_Version.MARATHON))
            except Exception as error:
                print('[m2x]   skeleton of the piece %08X: %s' % (tag, error))
        own_points = m2x.markers(own)
        point = m2x.attach_point(own)
        for component, model in models:
            parts = m2x.read_model(pm, model, stages, detail)
            if not parts:
                continue
            label = 'piece_%08X' % model
            plates = {p.material: plates_of(p.material) for p in parts}
            record = {'entity': '%08X' % tag, 'below': ['%08X' % t for t in path], 'model': '%08X' % model, 'component': '%08X' % component.tag,
                      'parts': len(parts), 'vertices': int(sum(len(p.positions) for p in parts)), 'triangles': int(sum(len(p.triangles) for p in parts)),
                      'materials': sorted({'%08X' % p.material for p in parts}),
                      'bones': piece_skeleton.names if piece_skeleton else None,
                      'box_min': [round(float(x), 4) for x in np.min([p.positions.min(axis=0) for p in parts], axis=0)],
                      'box_max': [round(float(x), 4) for x in np.max([p.positions.max(axis=0) for p in parts], axis=0)]}
            # the piece alone, on its own skeleton (or on one bone)
            own_skeleton = piece_skeleton or handle
            file = '%s_%s.glb' % (name, label)
            export.build_glb(os.path.join(root, file), own_skeleton, [export.MeshSet(label, parts, own_skeleton, {}, '%08X' % model, plates)], [], label)
            record['file'] = file
            # the place of the piece in the weapon
            slot = slot_of.get(tag)
            record['slot'] = m2x.name_of(slot) if slot is not None else None
            record['point'] = m2x.name_of(point) if point is not None else None
            matrix, bone = None, 0
            if len(path) > 1:
                record['place'] = None
                record['note'] = 'not in the files of the weapon: an entity below the piece %08X' % path[-1]
            elif point is not None and point in points:
                bone = points[point][0]
                matrix = bind[bone] @ m2x.marker_matrix(points[point])
                if m2x.ATTACHMENT in own_points:
                    matrix = matrix @ np.linalg.inv(m2x.marker_matrix(own_points[m2x.ATTACHMENT]))
                record['place'] = 'the point %s of the weapon, on the bone %s' % (record['point'], skeleton.names[bone])
            elif point is None and slot is None:
                matrix = np.eye(4)
                record['place'] = 'the coordinates of the weapon, on the bone %s (a piece with no slot and no point)' % skeleton.names[0]
            else:
                record['place'] = None
                record['note'] = 'not in the files of the weapon: the weapon has no point %s' % record['point']
            if matrix is not None:
                record['matrix'] = [[round(float(x), 6) for x in row] for row in matrix]
                record['mesh'] = 'region%02d_%08X' % (len(weapon_sets), tag)
                weapon_sets.append(export.MeshSet(record['mesh'], moved(parts, matrix, bone), skeleton, {}, '%08X' % model, plates))
            manifest['pieces'].append(record)
            print('[m2x] piece %08X (entity %08X, slot %s): %d parts, %d triangles; %s' % (
                model, tag, record['slot'], record['parts'], record['triangles'], record['place'] or record['note']))

    # the clips of the weapon: each animation set that a component of the entity names
    clip_tags = []
    for c in components:
        for set_tag in m2x.tags_in(pm, c.data, m2x.ANIMATION_SET):
            for name_hash, clip in m2x.animation_set(pm, set_tag, t64):
                found = next((row for row in clip_tags if row[2] == clip), None)
                if found is None:
                    clip_tags.append((set_tag, [name_hash], clip))
                elif name_hash not in found[1]:
                    found[1].append(name_hash)
            # a set can have clips with no name row
            for clip in m2x.tags_in(pm, pm.read(set_tag), m2x.CLIP, t64):
                if not any(row[2] == clip for row in clip_tags):
                    clip_tags.append((set_tag, [], clip))
    clips = []
    for order, (set_tag, name_hashes, clip) in enumerate(clip_tags):
        label = 'clip_%03d_%s' % (order, m2x.name_of(name_hashes[0]) if name_hashes else '%08X' % clip)
        record = {'name': label, 'tag': '%08X' % clip, 'set': '%08X' % set_tag, 'order': order, 'package': pm.pkg_name(clip),
                  'animation_names': [m2x.name_of(h) for h in name_hashes]}
        try:
            decoded = rig.decode(dump(clip), label)
        except Exception as error:
            record['error'] = '%s: %s' % (type(error).__name__, error)
            print('[m2x] clip %08X did not decode: %s' % (clip, record['error']))
            manifest['clips'].append(record)
            continue
        record.update(frames=int(decoded.frame_count), seconds=round(decoded.frame_count / FRAME_RATE, 3), nodes=int(decoded.node_count),
                      animation_hash='%08X' % decoded.animation_hash, codecs=list(decoded.codecs), additive=bool(decoded.additive),
                      moving_bones=[skeleton.names[i] for i in np.nonzero(decoded.animated)[0] if i < len(skeleton)])
        if decoded.additive:
            decoded.name = record['name'] = label + '_add'
        manifest['clips'].append(record)
        if decoded.node_count != len(skeleton):
            # the set also has clips for a skeleton with another bone count (another weapon of the family)
            record['note'] = 'not in the weapon file: the clip has %d nodes and the skeleton has %d bones' % (decoded.node_count, len(skeleton))
            print('[m2x] clip %08X (%s): %d frames, %d nodes: for another skeleton' % (clip, ', '.join(record['animation_names']) or 'no name', record['frames'], record['nodes']))
            continue
        clips.append((decoded, record))
        print('[m2x] clip %08X (%s): %d frames, moving bones: %s' % (clip, ', '.join(record['animation_names']) or 'no name', record['frames'], ', '.join(record['moving_bones']) or 'none'))
    manifest['weapon_clips'] = manifest['clips']

    file = '%s_weapon.glb' % name
    export.build_glb(os.path.join(root, file), skeleton, weapon_sets, [c for c, _ in clips], name)
    manifest['weapon_file'] = manifest['files']['weapon'] = file
    print('[m2x] %s: %d of %d pieces, %d textures, %d of %d clips (%d with an error)' % (
        os.path.join(root, file), len(weapon_sets), len(manifest['pieces']), len(textures), len(clips), len(manifest['clips']),
        sum(1 for c in manifest['clips'] if 'error' in c)))

    manifest['first_person'] = []
    arms = arm_entities(pm, components, t64)
    manifest['arm_entities'] = [{'number': i, 'name': n, 'entity': '%08X' % e} for i, (n, e) in enumerate(arms)]
    if arms and not a.no_first_person:
        first_person(pm, t64, a, root, name, title, manifest, components, skeleton, weapon_sets, clips, arms, dump)
    with open(os.path.join(root, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)


def first_person(pm, t64, a, root, name, title, manifest, components, weapon_skeleton, weapon_sets, weapon_clips, arms, dump):
    """The first-person file: the rig of an arm entity, the pieces, and the clips of the graph for this weapon."""
    arm_name, arm = arms[min(a.arms, len(arms) - 1)]
    own = m2x.read_entity(pm, arm)
    skeleton_c = next((c for c in own if c.kind == m2x.SKELETON), None)
    rig_c = next((c for c in own if c.kind == m2x.RIG), None)
    animation = next((c for c in own if c.kind == m2x.ANIMATION), None)
    if skeleton_c is None or rig_c is None or animation is None:
        print('[m2x] the arm entity %08X has no skeleton, no rig or no animation component: no first-person file' % arm)
        return
    rig = anim.Rig(dump(skeleton_c.tag), dump(rig_c.tag), 'marathon')
    skeleton = skeleton_data(skeleton_c.tag, rig.skeleton)
    set_tag = m2x.tags_in(pm, animation.data, m2x.ANIMATION_SET)[0]
    graph_tag = m2x.tags_in(pm, animation.data, m2x.GRAPH)[0]
    trees_tag = m2x.tags_in(pm, animation.data, m2x.TAG_TREES)[0]
    dimensions, trees = m2x.tag_trees(pm.read(trees_tag))
    tree = trees[dimensions[m2x.WEAPON_DIMENSION]]
    pair = m2x.weapon_tag_pair(components, tree)
    tags = m2x.tag_chain(tree, pair[1]) if pair else []
    set_clips, entries = m2x.set_tables(pm, set_tag, t64)
    states = m2x.read_graph(pm.read(graph_tag), tags)
    print('[m2x] first person: arm entity %08X (%s), %d bones, set %08X (%d clips, %d entries), graph %08X (%d states), weapon tags %s' % (
        arm, arm_name, len(skeleton), set_tag, len(set_clips), len(entries), graph_tag, len(states), ', '.join(word(t) for t in tags) or 'none'))

    # each clip that a state has for this weapon, one time, in the order of the set
    wanted = sorted({entries[e][1] for _, _, choices in states for _, _, items in choices for e, _ in items
                     if e < len(entries) and entries[e][1]}, key=lambda t: set_clips.index(t) if t in set_clips else len(set_clips))
    base, base_name = None, None
    for tag in wanted:
        try:
            data, tracks = rig.controls(dump(tag))
        except Exception:
            continue
        if data.animation_header.node_count >= rig.bone_count and not rig.is_additive(tracks):
            base, base_name = tracks, 'fp_%03d_%08X' % (set_clips.index(tag), tag)
            break
    weapon_bones = [skeleton.index_of(h) for h in weapon_skeleton.hashes[1:]]
    clips, records, name_of_clip = [], [], {}
    for tag in wanted:
        order = set_clips.index(tag) if tag in set_clips else -1
        label = 'fp_%03d_%08X' % (order, tag)
        record = {'name': label, 'tag': '%08X' % tag, 'set': '%08X' % set_tag, 'order': order, 'package': pm.pkg_name(tag)}
        try:
            clip = rig.decode(dump(tag), label, base)
        except Exception as error:
            record['error'] = '%s: %s' % (type(error).__name__, error)
            print('[m2x]   clip %08X did not decode: %s' % (tag, record['error']))
            records.append(record)
            continue
        if clip.additive:
            clip.name = record['name'] = label + '_add'
            record['additive'] = True
            record['shown_on'] = base_name
        record.update(animation_hash='%08X' % clip.animation_hash, frames=int(clip.frame_count), seconds=round(clip.frame_count / FRAME_RATE, 3),
                      nodes=int(clip.node_count), codecs=list(clip.codecs), moving_bones=int(clip.animated.sum()),
                      moving_weapon_bones=[skeleton.names[i] for i in weapon_bones if 0 <= i < len(clip.animated) and clip.animated[i]])
        name_of_clip[tag] = record['name']
        records.append(record)
        if clip.node_count != len(skeleton):
            record['note'] = 'not in the file: the clip has %d nodes and the rig has %d bones' % (clip.node_count, len(skeleton))
            continue
        clips.append(clip)

    # the clips of the weapon entity on this skeleton: the body at rest, the gun parts as in the clip
    slot_of = {i: skeleton.index_of(h) for i, h in enumerate(weapon_skeleton.hashes) if i > 0}
    difference = max((float(np.abs(weapon_skeleton.local[i] - skeleton.local[k]).max()) for i, k in slot_of.items() if k >= 0), default=0.0)
    for clip, source in weapon_clips:
        label = 'weapon_%03d_%s' % (source['order'], source['tag'])
        out = rest_clip(skeleton, label + ('_add' if clip.additive else ''), clip.rotations.shape[1])
        for i, k in slot_of.items():
            if k >= 0:
                out.scales[k], out.rotations[k], out.translations[k] = clip.scales[i], clip.rotations[i], clip.translations[i]
                out.animated[k] = clip.animated[i]
        out.animation_hash, out.additive = clip.animation_hash, clip.additive
        clips.append(out)
        records.append({'name': out.name, 'tag': source['tag'], 'set': source['set'], 'order': source['order'], 'frames': source['frames'],
                        'seconds': source['seconds'], 'nodes': len(skeleton), 'animation_names': source['animation_names'],
                        'moving_bones': int(out.animated.sum()), 'moving_weapon_bones': [b for b in source['moving_bones'] if b != weapon_skeleton.names[0]],
                        'weapon_clip': True, **({'additive': True} if clip.additive else {})})

    # the states, in the form of destiny/port/tools/d2states.py
    by_tag = {r['tag']: r for r in records if 'error' not in r and not r.get('weapon_clip')}
    state_records = []
    for index, hashes, choices in states:
        state = {'index': index, 'names': sorted(gr.STATE_NAMES[h] for h in hashes if h in gr.STATE_NAMES) or [w for w in (word(h) for h in hashes) if not re.fullmatch('[0-9A-F]{8}', w)],
                 'hashes': ['%08X' % h for h in hashes], 'choices': []}
        for conditions, tag, items in choices:
            rows = []
            for e, weight in items:
                r = by_tag.get('%08X' % entries[e][1]) if e < len(entries) else None
                if r:
                    rows.append({'clip': r['name'], 'threshold': weight, 'frames': r['frames'], 'additive': bool(r.get('additive')),
                                 'entry': e, 'entry_name': word(entries[e][0]), 'moving_weapon_bones': r.get('moving_weapon_bones', [])})
            if rows:
                state['choices'].append({'condition': ' '.join(w for w in (word(v) for _, v in conditions) if w),
                                         'condition_hashes': ['%X:%08X' % c for c in conditions],
                                         'weapon_tag': word(tag) if tag else '', 'clips': rows})
        state_records.append(state)

    mesh_sets, body = list(weapon_sets), []
    if a.hands:
        hands, record = hands_of(a.hands, skeleton)
        mesh_sets.append(hands)
        body.append(record)
    sights = next((c for s in state_records if 'iron_sight_idle' in s['names'] for ch in s['choices'] for c in ch['clips'][:1]), None)
    named = [dataclasses.replace(c, name='iron_sight_idle') for c in clips if sights and c.name == sights['clip']]
    file = '%s_first_person.glb' % name
    size = export.build_glb(os.path.join(root, file), skeleton, mesh_sets, clips, '%s_first_person' % name, export.camera_markers(skeleton, named))
    manifest['files']['first_person'] = file
    manifest['first_person'].append({
        'entity': '%08X' % arm, 'source_name': arm_name, 'skeleton': '%08X' % skeleton_c.tag, 'rig': '%08X' % rig_c.tag,
        'animation_set': '%08X' % set_tag, 'graph': '%08X' % graph_tag, 'tag_trees': '%08X' % trees_tag,
        'weapon_tag_pair': [word(t) for t in pair] if pair else None, 'weapon_tags': [word(t) for t in tags],
        'bones': skeleton.names, 'file': file, 'set_file': None,
        'camera_bone': export.CAMERA_BONE if export.CAMERA_BONE in skeleton.names else None,
        'weapon_bone_rest_difference': round(difference, 6), 'body': body, 'states': state_records, 'clips': records})
    with open(os.path.join(root, 'states.json'), 'w') as f:
        json.dump({'name': title, 'game': 'Marathon', 'rigs': [{'file': file, 'entity': '%08X' % arm, 'graph': '%08X' % graph_tag,
                                                              'is_rig_of_the_weapon': True, 'tags': [word(t) for t in tags],
                                                              'states': state_records}]}, f, indent=1)
    print('[m2x] %s: %.1f MB, %d bones, %d clips of the arms, %d clips of the weapon; the rest places of the gun parts differ by %.6f' % (
        os.path.join(root, file), size / 1e6, len(skeleton), len(clips) - len(weapon_clips), len(weapon_clips), difference))
    for state in state_records:
        label = '/'.join(state['names']) or 'state_' + (min(state['hashes']) if state['hashes'] else str(state['index']))
        for choice in state['choices']:
            for clip in choice['clips']:
                print('[m2x]   %-28s %-22s tag %-6s %-22s %4d frames  %.3f %s' % (
                    label[:28], choice['condition'][:22] or '-', choice['weapon_tag'] or '-', clip['clip'], clip['frames'], clip['threshold'],
                    ','.join(clip['moving_weapon_bones'])))


if __name__ == '__main__':
    main()
